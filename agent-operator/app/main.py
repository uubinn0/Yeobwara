from fastapi import FastAPI, Request, HTTPException
from app.deploy import deploy_agent
from app.config import NAMESPACE
from kubernetes import config
from kubernetes.client import CoreV1Api
import asyncio

app = FastAPI()

# 쿠버네티스 클러스터 인증 세팅
config.load_incluster_config()

@app.get("/health")
def health_check():
    return {"status": "ok"}

async def wait_for_pod_change(core_v1: CoreV1Api, old_pod_name: str, label_selector: str, max_retries: int = 30) -> str:
    for _ in range(max_retries):
        pods = core_v1.list_namespaced_pod(
            namespace=NAMESPACE,
            label_selector=label_selector
        )
        if pods.items:
            pod = pods.items[0]
            # 이전 Pod가 종료되었고, 새로운 Pod가 Running 상태인지 확인
            if pod.metadata.name != old_pod_name and pod.status.phase == "Running":
                return pod.metadata.name
        await asyncio.sleep(1)
    raise HTTPException(status_code=500, detail="Pod recreation timeout")

@app.post("/deploy")
async def deploy_user_server(request: Request):
    try:
        data = await request.json()

        user_id = data["user_id"]
        env_vars = data.get("env", [])

        # 비동기 함수 호출
        result = await deploy_agent(user_id, env_vars)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))