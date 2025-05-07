from kubernetes import client
from app.config import NAMESPACE, AGENT_IMAGE

def deploy_agent(user_id: str, env_vars: list) -> str:
    name = f"agent-{user_id}"

    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    # Deployment 스펙 정의 (RollingUpdate 전략 포함)
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
    # replace (존재 시 롤링 업데이트) or create (없을 시 신규 생성)
    try:
        apps_v1.replace_namespaced_deployment(name=name, namespace=NAMESPACE, body=deployment)
        first_create = False
    except client.exceptions.ApiException as e:
        if e.status == 404:
            apps_v1.create_namespaced_deployment(namespace=NAMESPACE, body=deployment)
            first_create = True
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
        core_v1.create_namespaced_service(namespace=NAMESPACE, body=service)

    # service_url = f"http://{name}.{NAMESPACE}.svc.cluster.local"
    # return service_url
