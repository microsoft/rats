from oneml.lorenzo.pipelines import (
    TypeNamespaceClient,
    NamespacedStorage,
    PipelineStep,
    PipelineStorage
)
from ._input_data import InputDataStep, InputLabelsStep
from ._logistic_regression_train import LogisticRegressionTrainStep, LogisticRegressionParams
from ._matrix import RealsMatrix
from ._standardization_train import StandardizationTrainStep, StandardizationParams
from ._vector import RealsVector


class StandardizedLogisticRegressionPipeline(PipelineStep):

    _storage: PipelineStorage
    _namespace_client: TypeNamespaceClient

    _batch_size: int
    _learning_rate: float

    def __init__(
            self,
            storage: PipelineStorage,
            namespace_client: TypeNamespaceClient,
            batch_size: int,
            learning_rate: float):
        self._storage = storage
        self._namespace_client = namespace_client
        self._batch_size = batch_size
        self._learning_rate = learning_rate

    def execute(self) -> None:
        input_namespace = self._namespace_client.get_namespace("input-data")
        input_storage = NamespacedStorage(
            storage=self._storage,
            namespace=input_namespace)

        input_labels_step = InputLabelsStep(storage=input_storage)
        input_labels_step.execute()

        input_data_step = InputDataStep(storage=input_storage)
        input_data_step.execute()

        print(input_storage.load(RealsVector))  # input labels
        print(input_storage.load(RealsMatrix))  # input data (FEATURES)

        standardization_namespace = self._namespace_client.get_namespace("standardization-data")
        standardization_storage = NamespacedStorage(
            storage=self._storage,
            namespace=standardization_namespace)
        standardization_step = StandardizationTrainStep(
            storage=standardization_storage,
            matrix=input_storage.load(RealsMatrix),
        )
        standardization_step.execute()

        print(standardization_storage.load(StandardizationParams))
        print(standardization_storage.load(RealsMatrix))

        logistic_regression_namespace = self._namespace_client.get_namespace(
            "logistic-regression-data")
        logistic_regression_storage = NamespacedStorage(
            storage=self._storage,
            namespace=logistic_regression_namespace,
        )
        logistic_regression_step = LogisticRegressionTrainStep(
            storage=logistic_regression_storage,
            data=standardization_storage.load(RealsMatrix),
            labels=input_storage.load(RealsVector),
            batch_size=self._batch_size,
            learning_rate=self._learning_rate,
        )
        logistic_regression_step.execute()

        print(logistic_regression_storage.load(LogisticRegressionParams))
        print(logistic_regression_storage.load(RealsVector))


