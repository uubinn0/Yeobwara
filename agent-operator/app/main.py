from fastapi import FastAPI, Request, HTTPException
from app.deploy import deploy_agent

app = FastAPI()

@app.post("/deploy")
async def deploy_user_server(request: Request):
    try:
        data = await request.json()
        user_id = data["user_id"]
        env_vars = data.get("env", [])
        pod_name = await deploy_agent(user_id, env_vars)
        return {"pod_name": pod_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
