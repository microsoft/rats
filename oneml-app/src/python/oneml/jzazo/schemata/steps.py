from dataclasses import dataclass, field
from typing import Any, List

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING


@dataclass
class StandardizedLogisticRegressionTrainConf:
    _target_: str = (
        "oneml.lorenzo.pipelines._example_oneml._pipeline.StandardizedLogisticRegressionPipeline"
    )
    defaults: List[Any] = field(
        default_factory=lambda: [
            {"/storage@_global_.pipeline.stzlr.storage": "namespace"},
            {"/storage@_global_.pipeline.stzlr.namespace_client": "namespace_client"},
        ]
    )
    storage: Any = MISSING
    namespace_client: Any = MISSING
    batch_size: int = MISSING
    learning_rate: float = MISSING


@dataclass
class StandardizationTrainConf:
    _target_: str = (
        "oneml.lorenzo.pipelines._example_oneml._standardization_train.StandardizationTrainStep"
    )
    storage: Any = MISSING
    matrix: Any = MISSING


@dataclass
class StandardizationPredictConf:
    _target_: str = (
        "oneml.lorenzo.pipelines._example_oneml._standardization_train.StandardizationPredictStep"
    )
    storage: Any = MISSING
    matrix: Any = MISSING
    mean: Any = MISSING
    scale: Any = MISSING


@dataclass
class LogisticRegressionTrainConf:
    _target_: str = (
        "oneml.lorenzo.pipelines._example_oneml._standardization_train.StandardizationTrainStep"
    )
    storage: Any = MISSING
    data: Any = MISSING
    labels: Any = MISSING
    batch_size: int = MISSING
    learning_rate: float = MISSING


@dataclass
class LogisticRegressionPredictConf:
    _target_: str = (
        "oneml.lorenzo.pipelines._example_oneml._standardization_train.StandardizationTrainStep"
    )
    storage: Any = MISSING
    data: Any = MISSING
    labels: Any = MISSING
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
