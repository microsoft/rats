from functools import partial

from oneml.lorenzo.pipelines import (
    PipelineStep,
    TypeNamespaceClient,
    NamespacedStorage,
    PipelineStorage
)
from ._search_space import TrainerParameterSearchSpace, TrainerHyperparameters


class HyperparameterSearchStep(PipelineStep):

    _storage: PipelineStorage
    _namespace_client: TypeNamespaceClient
    _search_space: TrainerParameterSearchSpace

    def __init__(
            self,
            storage: PipelineStorage,
            namespace_client: TypeNamespaceClient,
            search_space: TrainerParameterSearchSpace,
            pipeline_factory: partial):
        self._storage = storage
        self._namespace_client = namespace_client
        self._search_space = search_space
        self._pipeline_factory = pipeline_factory

    def execute(self) -> None:
        for i, hyperparams in enumerate(self._search_space.values()):
            params_namespace = self._namespace_client.get_namespace(f"hyperparams-{i}")
            params_storage = NamespacedStorage(
                storage=self._storage,
                namespace=params_namespace)
            params_storage.save(TrainerHyperparameters, hyperparams)
            pipeline = self._pipeline_factory(
                storage=params_storage,
                batch_size=hyperparams.batch_size,
                learning_rate=hyperparams.learning_rate,
            )
            pipeline.execute()
