from dataclasses import dataclass
from typing import Any

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING

from .storage import NamespacedStorageConf, TypeNamespaceClientConf


@dataclass
class StandardizedLogisticRegressionTrainConf:
    _target_: str = (
        "oneml.lorenzo.pipelines._example_oneml._pipeline.StandardizedLogisticRegressionPipeline"
    )
    storage: Any = NamespacedStorageConf()
    namespace_client: Any = TypeNamespaceClientConf()
    batch_size: int = MISSING
    learning_rate: float = MISSING


@dataclass
class StandardizationTrainConf:
    _target_: str = (
        "oneml.lorenzo.pipelines._example_oneml._standardization_train.StandardizationTrainStep"
    )
    storage: Any = NamespacedStorageConf()
    X: Any = MISSING


@dataclass
class StandardizationPredictConf:
    _target_: str = (
        "oneml.lorenzo.pipelines._example_oneml._standardization_train.StandardizationPredictStep"
    )
    storage: Any = NamespacedStorageConf()
    X: Any = MISSING
    mean: Any = MISSING
    scale: Any = MISSING


@dataclass
class LogisticRegressionTrainConf:
    _target_: str = "oneml.lorenzo.pipelines._example_oneml._logistic_regression_train.LogisticRegressionTrainStep"
    storage: Any = NamespacedStorageConf()
    X: Any = MISSING
    Y: Any = MISSING
    batch_size: int = MISSING
    learning_rate: float = MISSING


@dataclass
class LogisticRegressionPredictConf:
    _target_: str = "oneml.lorenzo.pipelines._example_oneml._logistic_regression_train.LogisticRegressionPredictStep"
    storage: Any = NamespacedStorageConf()
    X: Any = MISSING
    Y: Any = MISSING
    weight: Any = MISSING
    bias: Any = MISSING


def register_configs(cs: ConfigStore) -> None:
    cs.store(group="step", name="standardization_train", node=StandardizationTrainConf)
    cs.store(group="step", name="standardization_predict", node=StandardizationPredictConf)
    cs.store(group="step", name="logistic_regression_train", node=LogisticRegressionTrainConf)
    cs.store(group="step", name="logistic_regression_predict", node=LogisticRegressionPredictConf)
    cs.store(
        group="step",
        name="standardized_logistic_regression_train",
        node=StandardizedLogisticRegressionTrainConf,
    )
