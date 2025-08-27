from kubernetes import client
from kubernetes.client.rest import ApiException

from rats import apps


class CreateNamespace(apps.Executable):
    _k8s_client: client.CoreV1Api
    _namespace_name: str

    def __init__(
        self,
        k8s_client: client.CoreV1Api,
        namespace_name: str,
    ) -> None:
        self._k8s_client = k8s_client
        self._namespace_name = namespace_name

    def execute(self) -> None:
        # Attempt to create the namespace directly
        namespace_manifest = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=self._namespace_name)
        )

        try:
            self._k8s_client.create_namespace(body=namespace_manifest)
        except ApiException as e:
            if e.status == 409:
                # Namespace already exists (Conflict), which is fine
                pass
            else:
                # Re-raise other API exceptions
                raise
