from oneml.lorenzo.pipelines import (
    DeferredChainBuilder,
    NamespacedStorage,
    PipelineStep,
    PipelineStorage,
    TypeNamespaceClient,
)

from ._iteration_params import IterationParameters, IterationParametersStep
from ._pipeline_iteration import ExamplePipelineIteration


class ExamplePipeline(PipelineStep):
    _storage: PipelineStorage
    _namespace_client: TypeNamespaceClient

    def __init__(self, storage: PipelineStorage, namespace_client: TypeNamespaceClient):
        self._storage = storage
        self._namespace_client = namespace_client

    def execute(self) -> None:
        for iteration_num in range(5):
            iteration_namespace = self._namespace_client.get_namespace(
                name=f"iteration-{iteration_num}")

            iteration_storage = NamespacedStorage(
                storage=self._storage,
                namespace=iteration_namespace)

            builder = DeferredChainBuilder()

            builder.add(lambda: IterationParametersStep(
                output_storage=iteration_storage,
                iteration_number=iteration_num))

            builder.add(lambda: ExamplePipelineIteration(
                storage=iteration_storage,
                namespace_client=self._namespace_client,
                parameters=iteration_storage.load(IterationParameters)
            ))

            builder.build().execute()
