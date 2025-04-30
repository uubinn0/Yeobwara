from fastapi import FastAPI, Request, HTTPException
from app.deploy import deploy_agent
from kubernetes import config

app = FastAPI()

# 쿠버네티스 클러스터 인증 세팅
config.load_incluster_config()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/deploy")
async def deploy_user_server(request: Request):
    try:
        data = await request.json()
        user_id = data["user_id"]
        env_vars = data.get("env", [])
        service_url = deploy_agent(user_id, env_vars)
        return {"service_url": service_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
