from dataclasses import dataclass, field
from typing import Any

from hydra_zen import ZenStore, hydrated_dataclass, just
from hydra_zen.typing import ZenConvert as zc
from omegaconf import MISSING

from oneml.services import ServiceId

from ..ml import EstimatorConf
from ..ux import (
    CollectionDependencyOpConf,
    CombinedConf,
    EntryDependencyOpConf,
    PipelineDependencyOpConf,
    TaskConf,
)


@hydrated_dataclass(ServiceId)
class ServiceIdConf:
    name: str = MISSING


@dataclass
class TaskParametersConf:
    config: dict[str, Any] | None = None
    service_ids: dict[str, ServiceIdConf] | None = None


@dataclass
class PipelineConfig:
    task_parameters: dict[str, TaskParametersConf] = field(default_factory=dict)
    pipeline: Any = None


def register_configs(store: ZenStore) -> None:
    store(TaskConf(), name="base", group="task")
    store(CombinedConf(), name="base", group="combined")
    store(EstimatorConf(), name="base", group="estimator")
    store(EntryDependencyOpConf(), name="entry", group="dependency")
    store(CollectionDependencyOpConf(), name="collection", group="dependency")
    store(PipelineDependencyOpConf(), name="pipeline", group="dependency")
    store(ServiceIdConf(), name="service_id")
    store(TaskParametersConf, name="task_parameters")
    store(just(PipelineConfig(), zen_convert=zc(dataclass=True)), name="pipeline_config")
