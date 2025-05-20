import os
from fastapi import FastAPI, HTTPException
from agents import Agent, Runner, set_default_openai_client, OpenAIChatCompletionsModel, RunConfig, ModelSettings
from agents.mcp.server import MCPServerStdio
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

#############################################

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

GMS_API_KEY = os.getenv("GMS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY                   # Openai의 트레이싱을 하는데 사용할 개인 Openai Key
base_url="https://gms.p.ssafy.io/gmsapi/api.openai.com/v1"
gms_client = AsyncOpenAI(api_key=GMS_API_KEY, base_url=base_url)    # 실제 API 호출은 GMS를 사용
set_default_openai_client(gms_client, use_for_tracing=False)        # 트레이싱에는 GMS를 사용하지 않음

# gms_client 를 사용한 모델 지정 
gms_model = OpenAIChatCompletionsModel(
    model="gpt-4.1",
    # model="o3-mini",
    openai_client=gms_client,
)

#############################################


# 요청 모델 정의
class AgentRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    use_conversation_context: Optional[bool] = False

# MCP 서버들 설정
MCP_SERVER_CONFIG = {
    "notion": {
        "type": "stdio",
        "params": {"command": "mcp-notion-server", "args": ["--enabledTools=notion_retrieve_block,notion_retrieve_block_children,notion_append_block_children"], 
                   "env": {"NOTION_API_TOKEN": os.getenv("NOTION_API_TOKEN", "")}}
    },
    "gitlab": {
        "type": "stdio",
        "params": {"command": "mcp-gitlab", "args": [], "env": {"GITLAB_PERSONAL_ACCESS_TOKEN": os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN", ""), "GITLAB_API_URL": os.getenv("GITLAB_API_URL", ""), "GITLAB_READ_ONLY_MODE": os.getenv("GITLAB_READ_ONLY_MODE", "true")}}
    },
    "duckduckgo-search": {
        "type": "stdio",
        "params": { "command": "duckduckgo-mcp-server", "args": [], "env": {}}
    },
    "korean-spell-checker": {
        "type": "stdio",
        "params": { "command": "mcp-korean-spell", "args": [], "env": {}}
    },
    "sequentialthinking": {
        "type": "stdio",
        "params": {"command": "mcp-server-sequential-thinking", "args": [], "env": {}}
    },
    "airbnb": {
        "type": "stdio",
        "params": {"command": "mcp-server-airbnb", "args": ["--ignore-robots-txt"], "env": {}}
    },
    "github": {
        "type": "stdio",
        "params": {"command": "mcp-server-github", "args": [], "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")}}
        # "params": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")}}
    },
    "kakao-map": {
        "type": "stdio",
        "params": {"command": "node", "args": ["/srv/mcp-server-kakao-map/dist/index.js"],
        "env": {"KAKAO_API_KEY": os.getenv("KAKAO_API_KEY", "")}
        }
    },
    "figma": {
      "type": "stdio",
      "params": {"command": "figma-developer-mcp",
        "args": [f"--figma-api-key={os.getenv('FIGMA_API_KEY', '')}", "--stdio"], "env": {}
        }
    },
    "paper-search": {
      "type": "stdio",
      "params": {"command": "uv", 
                 "args": ["run", "--directory", "/srv/paper-search-mcp", "-m", "paper_search_mcp.server"], 
                 "env": {}}
    },
    # "chess-local": {
    #   "type": "stdio",
    #   "params": {"command": "uv",
    #     "args": ["--directory", "/srv/chess-mcp", "run", "src/chess_mcp/main.py"],"env": {}}
    # },

    "dart-mcp": {
        "type": "stdio",
        "params": {"command": "uv",
            "args": ["run", "--directory", "/srv/dart-mcp", "dart.py"],
            "env": {"DART_API_KEY": os.getenv("DART_API_KEY", "")}}
    },


}

# 환경변수 MCP_SERVICES 기반으로 사용할 서비스만 필터링
services_env = os.getenv("MCP_SERVICES", "")
if services_env:
    allowed = [s.strip() for s in services_env.split(",") if s.strip()]
    MCP_SERVER_CONFIG = {k: v for k, v in MCP_SERVER_CONFIG.items() if k in allowed}

agent: Agent | None = None
servers: list[MCPServerStdio] = []

def format_conversation_history(history: List[Dict[str, Any]]) -> str:
    """대화 히스토리를 컨텍스트 문자열로 포맷팅"""
    if not history:
        return ""
    
    formatted_parts = ["이전 대화 내역:"]
    for item in history[-5:]:  # 최근 5개 대화만 사용
        user_msg = item.get('user', '')
        assistant_msg = item.get('assistant', '')
        
        if user_msg and assistant_msg:
            formatted_parts.append(f"사용자: {user_msg}")
            formatted_parts.append(f"어시스턴트: {assistant_msg}")
    
    return "\n".join(formatted_parts)

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
        instructions = f"Use the tools to achieve the task. Consider the conversation history when provided. Today's date is {date.today().isoformat()}. Answer in markdown format.",
        model=gms_model,
        mcp_servers=servers,
    )

# 앱 종료 시 모든 서버 정리
@app.on_event("shutdown")
async def shutdown_event():
    for srv in servers:
        await srv.cleanup()

# 메시지 처리 핸들러: 단순히 global agent 사용
# @app.post("/agent-query")
# async def query_agent(payload: dict):
#     if agent is None: raise HTTPException(503, "Agent가 초기화되지 않았습니다.")
#     text = payload.get("text")
#     if not text: raise HTTPException(400, "'text' 필드가 필요합니다.")
#     result = await Runner.run(agent, text)
#     return {"response": result.final_output}

# 메시지 처리 핸들러: Backend에서 conversation_history를 전달받아 처리
@app.post("/agent-query")
async def query_agent(payload: AgentRequest):
    if agent is None: 
        raise HTTPException(503, "Agent가 초기화되지 않았습니다.")
    
    text = payload.text
    
    # 대화 히스토리가 있는 경우 컨텍스트로 추가
    enhanced_text = text
    if payload.conversation_history and payload.use_conversation_context:
        conversation_context = format_conversation_history(payload.conversation_history)
        if conversation_context:
            enhanced_text = f"{conversation_context}\n\n현재 질문: {text}"
    
    try:
        # Agent 실행
        result = await Runner.run(agent, enhanced_text)
        response = result.final_output
        
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(500, f"Agent 처리 중 오류 발생: {str(e)}")

# 기존 호환성을 위한 단순 엔드포인트
@app.post("/agent-query-simple")
async def query_agent_simple(payload: dict):
    """기존 호환성을 위한 단순 텍스트 처리"""
    if agent is None: 
        raise HTTPException(503, "Agent가 초기화되지 않았습니다.")
    
    text = payload.get("text")
    if not text: 
        raise HTTPException(400, "'text' 필드가 필요합니다.")
    
    result = await Runner.run(agent, text)
    return {"response": result.final_output}