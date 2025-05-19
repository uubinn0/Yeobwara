import asyncio
from kubernetes import client, watch
from datetime import datetime
from app.config import NAMESPACE, AGENT_IMAGE
from kubernetes import config

# 클러스터 내부 설정 로드
config.load_incluster_config()

async def deploy_agent(user_id: str, env_vars: list) -> str:
    name = f"agent-{user_id}"
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    # 1) Deployment 객체 정의 (생성/업데이트 공통)
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=name, labels={"app": name}),
        spec=client.V1DeploymentSpec(
            replicas=1,
            strategy=client.V1DeploymentStrategy(
                type="RollingUpdate",
                rolling_update=client.V1RollingUpdateDeployment(
                    max_surge=1,
                    max_unavailable=0
                )
            ),
            selector={"matchLabels": {"app": name}},
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": name},
                    annotations={
                        # 롤링 업데이트 강제 트리거용 타임스탬프
                        "redeployTimestamp": datetime.utcnow().isoformat()
                    }
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="agent",
                            image=AGENT_IMAGE,
                            ports=[client.V1ContainerPort(container_port=8002)],
                            env=[client.V1EnvVar(name=e["name"], value=e["value"]) for e in env_vars],
                        )
                    ]
                )
            )
        )
    )

    # 2) 기존 Pod 목록 스냅샷
    existing = await asyncio.to_thread(
        lambda: {p.metadata.name for p in core_v1.list_namespaced_pod(
            namespace=NAMESPACE,
            label_selector=f"app={name}"
        ).items}
    )

    # 3) Deployment 생성 또는 교체
    try:
        await asyncio.to_thread(
            apps_v1.replace_namespaced_deployment,
            name=name,
            namespace=NAMESPACE,
            body=deployment
        )
        first_create = False
    except client.exceptions.ApiException as e:
        if e.status == 404:
            await asyncio.to_thread(
                apps_v1.create_namespaced_deployment,
                namespace=NAMESPACE,
                body=deployment
            )
            first_create = True
        else:
            raise

    # 4) 첫 생성일 때만 Service 생성
    if first_create:
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1ServiceSpec(
                selector={"app": name},
                ports=[client.V1ServicePort(port=80, target_port=8002)],
                type="ClusterIP"
            )
        )
        await asyncio.to_thread(
            lambda: core_v1.create_namespaced_service(namespace=NAMESPACE, body=service)
            if not any(s.metadata.name == name for s in core_v1.list_namespaced_service(namespace=NAMESPACE).items)
            else None
        )

    # 5) Watch로 새 Pod 감지
    def _watch_new_pod():
        w = watch.Watch()
        for event in w.stream(
            core_v1.list_namespaced_pod,
            namespace=NAMESPACE,
            label_selector=f"app={name}",
            timeout_seconds=120,
        ):
            pod = event['object']
            pod_name = pod.metadata.name

            # 기존에 없던 Pod 이름이고, Running 상태라면 리턴
            if pod_name not in existing and pod.status.phase == "Running":
                w.stop()
                return pod_name

        # 타임아웃 시 예외
        raise RuntimeError(f"새로운 Running 상태 Pod를 찾지 못했습니다 (existing={existing})")

    pod_name = await asyncio.to_thread(_watch_new_pod)
    return pod_name
