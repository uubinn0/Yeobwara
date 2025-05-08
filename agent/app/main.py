import os, openai
from fastapi import FastAPI, HTTPException
from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio
from types import MethodType

app = FastAPI()

# GMS 관련 환경변수
GMS_KEY = os.getenv("GMS_KEY")
GMS_API_BASE = os.getenv("GMS_API_BASE")
if not GMS_KEY or not GMS_API_BASE:
    raise RuntimeError("GMS_KEY 또는 GMS_API_BASE 환경 변수가 설정되지 않았습니다.")

# *************  ← 추가‧수정 START
# 1) GMS_BASE 보정: '/api.openai.com/v1' 세그먼트 없으면 자동 붙이기
if "api.openai.com" not in GMS_API_BASE:
    GMS_API_BASE = GMS_API_BASE.rstrip("/") + "/api.openai.com/v1"

os.environ["OPENAI_API_KEY"]  = GMS_KEY
os.environ["OPENAI_BASE_URL"] = GMS_API_BASE

# 2) OpenAI SDK에 프록시·키 주입
openai.api_key = GMS_KEY
try:
    openai.base_url = GMS_API_BASE      # openai ≥ 1.0
except AttributeError:
    openai.api_base = GMS_API_BASE      # openai 0.x 대응


# *************  ← 추가 START
# openai >=1.16 에서 responses.create → chat.completions.create 로 우회
async def _responses_proxy(self, **kwargs):
    return await openai.chat.completions.create(**kwargs)

try:
    openai.resources.responses.responses.Responses.create = MethodType(
        _responses_proxy, openai.resources.responses
    )
except AttributeError:
    pass  # <1.16 이면 해당 속성이 없음
# *************  ← 추가 END


# 3) /models 호출을 목업해 초기화 400 방지
def _dummy_models_list(*args, **kwargs):
    return [{"id": "gpt-4.1-mini"}]

try:
    openai.resources.models.list = _dummy_models_list   # openai ≥ 1.0
except AttributeError:
    openai.Model.list = _dummy_models_list              # openai 0.x
# *************  ← 추가‧수정 END

# MCP 서버들 설정
MCP_SERVER_CONFIG = {
    "github": {
        "type": "stdio",
        "params": {
            "command": "mcp-github-server",
            "args": [],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")},
        },
    },
    "notion": {
        "type": "stdio",
        "params": {
            "command": "mcp-notion-server",
            "args": [],
            "env": {"NOTION_API_TOKEN": os.getenv("NOTION_API_TOKEN", "")},
        },
    },
    "gitlab": {
        "type": "stdio",
        "params": {
            "command": "mcp-gitlab-server",
            "args": [],
            "env": {
                "GITLAB_PERSONAL_ACCESS_TOKEN": os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN", ""),
                "GITLAB_API_URL": os.getenv("GITLAB_API_URL", ""),
            },
        },
    },
}

# 환경변수 MCP_SERVICES 기반으로 사용할 서비스만 필터링
services_env = os.getenv("MCP_SERVICES", "")
if services_env:
    allowed = [s.strip() for s in services_env.split(",") if s.strip()]
    MCP_SERVER_CONFIG = {k: v for k, v in MCP_SERVER_CONFIG.items() if k in allowed}

agent: Agent | None = None
servers: list[MCPServerStdio] = []

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
        mcp_servers=servers,
    )

@app.on_event("shutdown")
async def shutdown_event():
    for srv in servers:
        await srv.cleanup()

@app.post("/agent-query")
async def query_agent(payload: dict):
    if agent is None:
        raise HTTPException(503, "Agent가 초기화되지 않았습니다.")
    text = payload.get("text")
    if not text:
        raise HTTPException(400, "'text' 필드가 필요합니다.")
    result = await Runner.run(agent, text)
    return {"response": result.final_output}
