# deploy.py
import asyncio
import time
from kubernetes import client
from app.config import NAMESPACE, AGENT_IMAGE

async def deploy_agent(user_id: str, env_vars: list) -> dict:
    name = f"agent-{user_id}"
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    
    # 현재 Deployment 상태 확인 (업데이트 전)
    try:
        current_deployment = await asyncio.to_thread(
            apps_v1.read_namespaced_deployment,
            name=name,
            namespace=NAMESPACE
        )
        current_generation = current_deployment.metadata.generation
        is_update = True
    except client.exceptions.ApiException as e:
        if e.status == 404:
            current_generation = 0
            is_update = False
        else:
            raise

    # 쿠버네티스 API 호출은 비동기가 아니므로 스레드풀에서 실행
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
                metadata=client.V1ObjectMeta(labels={"app": name}),
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
    
    # 쿠버네티스 API 호출을 비동기로 처리
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
            is_update = False
        else:
            raise

    # 첫 생성 시에만 Service 생성
    if first_create:
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1ServiceSpec(
                selector={"app": name},
                ports=[client.V1ServicePort(port=80, target_port=8002)],
                type="ClusterIP"
            )
        )
        try:
            await asyncio.to_thread(
                core_v1.create_namespaced_service, 
                namespace=NAMESPACE, 
                body=service
            )
        except client.exceptions.ApiException as e:
            if e.status != 409:  # 409(이미 존재) 에러는 무시하고 진행
                raise
    
    # 새 Pod 생성 감지 및 대기
    pod_name = await wait_for_new_pod(name, current_generation, is_update)
    
    return {
        "service_url": f"http://{name}.{NAMESPACE}.svc.cluster.local",
        "pod_name": pod_name
    }


async def wait_for_new_pod(name: str, current_generation: int, is_update: bool, timeout: int = 60):
    """새 Pod 생성을 감지하고 Running 상태까지 대기"""
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        await asyncio.sleep(2)
        
        # Deployment 상태 확인
        deployment = await asyncio.to_thread(
            apps_v1.read_namespaced_deployment,
            name=name,
            namespace=NAMESPACE
        )
        
        # 새 generation이 시작되었는지 확인
        if deployment.status.observed_generation > current_generation:
            # 최신 ReplicaSet 찾기
            replicasets = await asyncio.to_thread(
                apps_v1.list_namespaced_replica_set,
                namespace=NAMESPACE,
                label_selector=f"app={name}"
            )
            
            if replicasets.items:
                # 가장 최근 ReplicaSet 선택
                latest_rs = max(replicasets.items, 
                    key=lambda rs: int(rs.metadata.labels.get('pod-template-hash', '0'), 16))
                
                # 해당 ReplicaSet의 Pod 찾기
                pod_template_hash = latest_rs.metadata.labels.get('pod-template-hash')
                pods = await asyncio.to_thread(
                    core_v1.list_namespaced_pod,
                    namespace=NAMESPACE,
                    label_selector=f"app={name},pod-template-hash={pod_template_hash}"
                )
                
                if pods.items:
                    pod = pods.items[0]
                    # Pod가 Running 상태인지 확인
                    if pod.status.phase == "Running":
                        # Ready condition 확인
                        for condition in pod.status.conditions or []:
                            if condition.type == "Ready" and condition.status == "True":
                                return pod.metadata.name
    
    # 타임아웃 시 기존 방식으로 fallback
    pods = await asyncio.to_thread(
        core_v1.list_namespaced_pod,
        namespace=NAMESPACE,
        label_selector=f"app={name}"
    )
    if pods.items:
        return pods.items[0].metadata.name
    
    raise Exception(f"Pod 생성 실패: {name}")