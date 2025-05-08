import os
from fastapi import FastAPI, HTTPException
from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio

app = FastAPI()

# GMS 관련 환경변수
GMS_KEY = os.getenv("GMS_KEY")
GMS_API_BASE = os.getenv("GMS_API_BASE")
if not GMS_KEY or not GMS_API_BASE:
    raise RuntimeError("GMS_KEY 또는 GMS_API_BASE 환경 변수가 설정되지 않았습니다.")

###
os.environ["OPENAI_API_KEY"]  = GMS_KEY   # 기본 Client가 읽을 값
os.environ["OPENAI_API_BASE"] = GMS_API_BASE
import openai                      # ← 이제 import 시점에 키가 존재
openai.api_key  = GMS_KEY          # 구버전 호출 대비
openai.api_base = GMS_API_BASE
###


# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

# MCP 서버들 설정 ( 어떤 github 을 npx 로 띄울건지 )
MCP_SERVER_CONFIG = {
    "github": {
        "type": "stdio",
        "params": {"command": "mcp-github-server", "args": [], "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")}}
    },
    "notion": {
        "type": "stdio",
        "params": {"command": "mcp-notion-server", "args": [], "env": {"NOTION_API_TOKEN": os.getenv("NOTION_API_TOKEN", "")}}
    },
    "gitlab": {
        "type": "stdio",
        "params": {"command": "mcp-gitlab-server", "args": [], "env": {"GITLAB_PERSONAL_ACCESS_TOKEN": os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN", ""), "GITLAB_API_URL": os.getenv("GITLAB_API_URL", "")}}
    },
}

# 환경변수 MCP_SERVICES 기반으로 사용할 서비스만 필터링
services_env = os.getenv("MCP_SERVICES", "")
if services_env:
    allowed = [s.strip() for s in services_env.split(",") if s.strip()]
    MCP_SERVER_CONFIG = {k: v for k, v in MCP_SERVER_CONFIG.items() if k in allowed}

agent: Agent | None = None
servers: list[MCPServerStdio] = []

# 앱 시작 시 필요한 서버만 연결하고 Agent 초기화
@app.on_event("startup")
async def startup_event():
    global agent, servers
    for name, cfg in MCP_SERVER_CONFIG.items():
        srv = MCPServerStdio(params=cfg["params"], cache_tools_list=True, name=name)
        await srv.connect()
        servers.append(srv)
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to achieve the task",
        model="gpt-4.1-mini",
        mcp_servers=servers
    )

# 앱 종료 시 모든 서버 정리
@app.on_event("shutdown")
async def shutdown_event():
    for srv in servers:
        await srv.cleanup()

# 메시지 처리 핸들러: 단순히 global agent 사용
@app.post("/agent-query")
async def query_agent(payload: dict):
    if agent is None: raise HTTPException(503, "Agent가 초기화되지 않았습니다.")
    text = payload.get("text")
    if not text: raise HTTPException(400, "'text' 필드가 필요합니다.")
    result = await Runner.run(agent, text)
    return {"response": result.final_output}
