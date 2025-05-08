###########################################################################################
# main.py  ― GMS 프록시가  /v1/chat/completions  경로만 열린 상황 대응
###########################################################################################
import os, openai, httpx, json
from fastapi import FastAPI, HTTPException
from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio
from types import MethodType

app = FastAPI()

# ─────────────────────────────
# GMS 토큰 / 엔드포인트
# ─────────────────────────────
GMS_KEY      = os.getenv("GMS_KEY")
GMS_RAW_BASE = os.getenv("GMS_API_BASE")           # 예) …/v1/chat/completions
if not GMS_KEY or not GMS_RAW_BASE:
    raise RuntimeError("GMS_KEY 또는 GMS_API_BASE 미설정")
# ************* GMS base_url 고정 START
if GMS_RAW_BASE.rstrip("/").endswith("/chat/completions"):
    GMS_BASE_V1 = GMS_RAW_BASE.rsplit("/chat/completions", 1)[0]    # …/v1
else:
    GMS_BASE_V1 = GMS_RAW_BASE.rstrip("/")

# base_url 은 ‘/v1’ 까지만!  ↙︎
os.environ["OPENAI_BASE_URL"] = GMS_BASE_V1
openai.api_key  = GMS_KEY
openai.base_url = GMS_BASE_V1                        # openai ≥1.0
# ************* GMS base_url 고정 END

# ************* 모든 새 클라이언트도 같은 base 사용 START
from openai import AsyncOpenAI, OpenAI
from openai._client import _set_default_async_client, _set_default_client

_set_default_async_client(AsyncOpenAI(api_key=GMS_KEY, base_url=GMS_BASE_V1))
_set_default_client(OpenAI(api_key=GMS_KEY, base_url=GMS_BASE_V1))
# ************* 모든 새 클라이언트도 같은 base 사용 END




# ─────────────────────────────
# Responses → ChatCompletions 우회
# ─────────────────────────────
SAFE_KEYS = {
    "model","messages","stream","temperature","top_p","n",
    "logit_bias","max_tokens","stop",
    "presence_penalty","frequency_penalty","user"
}
async def _responses_proxy(self_or_cls, **kwargs):
    instr = kwargs.pop("instructions", None)
    for k in list(kwargs):
        if k not in SAFE_KEYS:
            kwargs.pop(k, None)                          # previous_response_id, include …

    if "messages" not in kwargs:
        if instr:
            kwargs["messages"] = [{"role": "system", "content": instr}]
        else:
            prompt = kwargs.pop("prompt", None) or kwargs.pop("input", None)
            if prompt is None:
                raise TypeError("messages / prompt / instructions 인자 필요")
            kwargs["messages"] = [{"role": "user", "content": prompt}]

    # 모델은 사용자가 넘겨준 값 그대로 두되, 없으면 기본 mini
    kwargs.setdefault("model", "gpt-4.1-mini")

    return await openai.chat.completions.create(**kwargs)

try:
    from openai.resources.responses import AsyncResponses, Responses
    AsyncResponses.create = MethodType(_responses_proxy, AsyncResponses)
    Responses.create      = MethodType(_responses_proxy, Responses)
except Exception:
    pass
setattr(openai.responses, "create", _responses_proxy)

# /v1/models 400 방지 목업
def _dummy_models_list(*args, **kwargs):
    return [{"id": "gpt-4.1-mini"}, {"id": "gpt-4o"}]
try:
    openai.resources.models.list = _dummy_models_list
except AttributeError:
    openai.Model.list = _dummy_models_list
# ─────────────────────────────

# MCP 서버 설정 (필요시 필터)
MCP_SERVER_CONFIG = {
    "github": {"type": "stdio",
               "params": {"command": "mcp-github-server", "args": [],
                          "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN","")}}},
    "notion": {"type": "stdio",
               "params": {"command": "mcp-notion-server", "args": [],
                          "env": {"NOTION_API_TOKEN": os.getenv("NOTION_API_TOKEN","")}}},
    "gitlab": {"type": "stdio",
               "params": {"command": "mcp-gitlab-server", "args": [],
                          "env": {"GITLAB_PERSONAL_ACCESS_TOKEN": os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN",""),
                                  "GITLAB_API_URL": os.getenv("GITLAB_API_URL","")}}},
}
svc_env = os.getenv("MCP_SERVICES", "")
if svc_env:
    allow = [s.strip() for s in svc_env.split(",") if s.strip()]
    MCP_SERVER_CONFIG = {k:v for k,v in MCP_SERVER_CONFIG.items() if k in allow}

agent: Agent | None = None
servers: list[MCPServerStdio] = []

@app.on_event("startup")
async def startup_event():
    global agent, servers
    for name,cfg in MCP_SERVER_CONFIG.items():
        srv = MCPServerStdio(params=cfg["params"], cache_tools_list=True, name=name)
        await srv.connect()
        servers.append(srv)
    agent = Agent(name="Assistant",
                  instructions="Use the tools to achieve the task",
                  model="gpt-4.1-mini",
                  mcp_servers=servers)

@app.on_event("shutdown")
async def shutdown_event():
    for srv in servers: await srv.cleanup()

@app.post("/agent-query")
async def query_agent(payload: dict):
    if agent is None: raise HTTPException(503, "Agent가 초기화되지 않았습니다.")
    text = payload.get("text")
    if not text: raise HTTPException(400, "'text' 필드가 필요합니다.")
    result = await Runner.run(agent, text)
    return {"response": result.final_output}
