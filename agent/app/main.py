import os, openai
from fastapi import FastAPI, HTTPException
from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio
from types import MethodType

app = FastAPI()

# ─────────────────────────────
# GMS 토큰‧엔드포인트 (ENV로 주입)
# ─────────────────────────────
GMS_KEY       = os.getenv("GMS_KEY")
GMS_API_BASE  = os.getenv("GMS_API_BASE")
if not GMS_KEY or not GMS_API_BASE:
    raise RuntimeError("GMS_KEY 또는 GMS_API_BASE 환경 변수가 없습니다.")

# ************* 변경 START
if "api.openai.com" not in GMS_API_BASE:
    GMS_API_BASE = GMS_API_BASE.rstrip("/") + "/api.openai.com/v1"

os.environ["OPENAI_API_KEY"]  = GMS_KEY
os.environ["OPENAI_BASE_URL"] = GMS_API_BASE

openai.api_key = GMS_KEY
try:
    openai.base_url = GMS_API_BASE
except AttributeError:
    openai.api_base = GMS_API_BASE
# ************* 변경 END

# *************  _responses_proxy 교체 START
SAFE_KEYS = {
    "model", "messages", "stream", "temperature", "top_p", "n",
    "logit_bias", "max_tokens", "stop",
    "presence_penalty", "frequency_penalty", "user"
}

async def _responses_proxy(self_or_cls, **kwargs):
    instr = kwargs.pop("instructions", None)                     # ①

    for k in list(kwargs):                                       # ②
        if k not in SAFE_KEYS:
            kwargs.pop(k, None)

    if "messages" not in kwargs:                                 # ③
        if instr:
            kwargs["messages"] = [{"role": "system", "content": instr}]
        else:
            prompt = kwargs.pop("prompt", None) or kwargs.pop("input", None)
            if prompt is None:
                raise TypeError("messages / prompt / instructions 인자 필요")
            kwargs["messages"] = [{"role": "user", "content": prompt}]

    kwargs.setdefault("model", "gpt-4.1-mini")                  # ④

    return await openai.chat.completions.create(**kwargs)        # ⑤

try:
    from openai.resources.responses import AsyncResponses, Responses
    AsyncResponses.create = MethodType(_responses_proxy, AsyncResponses)
    Responses.create      = MethodType(_responses_proxy, Responses)
except Exception:
    pass
setattr(openai.responses, "create", _responses_proxy)
# *************  _responses_proxy 교체 END

# ************* 추가 START
def _dummy_models_list(*args, **kwargs):
    return [{"id": "gpt-4.1-mini"}]

try:
    openai.resources.models.list = _dummy_models_list
except AttributeError:
    openai.Model.list = _dummy_models_list
# ************* 추가 END

# ─────────────────────────────
# MCP 서버 설정
# ─────────────────────────────
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

svc_env = os.getenv("MCP_SERVICES", "")
if svc_env:
    allow = [s.strip() for s in svc_env.split(",") if s.strip()]
    MCP_SERVER_CONFIG = {k: v for k, v in MCP_SERVER_CONFIG.items() if k in allow}

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
