from kubernetes import client
from app.config import NAMESPACE, AGENT_IMAGE

def deploy_agent(user_id: str, env_vars: list) -> str:
    name = f"agent-{user_id}"

    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    # ✅ 기존 Deployment/Service 삭제 (있으면)
    try:
        apps_v1.delete_namespaced_deployment(name=name, namespace=NAMESPACE)
        core_v1.delete_namespaced_service(name=name, namespace=NAMESPACE)
    except client.exceptions.ApiException as e:
        if e.status != 404:
            raise

    # Deployment 생성
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=name, labels={"app": name}),
        spec=client.V1DeploymentSpec(
            replicas=1,
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
    apps_v1.create_namespaced_deployment(namespace=NAMESPACE, body=deployment)

    # Service 생성
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            ports=[client.V1ServicePort(port=80, target_port=8002)],
            type="ClusterIP"
        )
    )
    core_v1.create_namespaced_service(namespace=NAMESPACE, body=service)

    service_url = f"http://{name}.{NAMESPACE}.svc.cluster.local"
    return service_url
