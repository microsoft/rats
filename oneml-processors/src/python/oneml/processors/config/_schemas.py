from dataclasses import dataclass, field
from typing import Any

from hydra_zen import ZenStore, hydrated_dataclass, just
from hydra_zen.typing import ZenConvert as zc
from omegaconf import MISSING

from oneml.processors.pipeline_operations import IProvidePipeline
from oneml.services import IProvideServices, ServiceId

from ..ml import EstimatorConf
from ..pipeline_operations import DuplicatePipelineConf
from ..ux import (
    CollectionDependencyOpConf,
    CombinedConf,
    EntryDependencyOpConf,
    PipelineDependencyOpConf,
    TaskConf,
    UPipeline,
)


@hydrated_dataclass(ServiceId)
class ServiceIdConf:
    name: str = MISSING


def get_pipeline(
    service_id: ServiceId[IProvidePipeline[UPipeline]], app: IProvideServices
) -> UPipeline:
    pipeline_provider: IProvidePipeline[Any] = app.get_service(service_id)
    return pipeline_provider()


@hydrated_dataclass(get_pipeline)
class GetPipelineFromApp:
    service_id: ServiceIdConf = MISSING
    app: Any = "${app}"


@dataclass
class PipelineConfig:
    configs: dict[str, Any] = field(default_factory=dict)
    service_ids: dict[str, ServiceIdConf] = field(default_factory=dict)
    pipeline: Any = None
    app: Any = MISSING


def register_configs(store: ZenStore) -> None:
    store(TaskConf(), name="base", group="task")
    store(CombinedConf(), name="base", group="combined")
    store(EstimatorConf(), name="base", group="estimator")
    store(DuplicatePipelineConf(), name="base", group="duplicate")
    store(EntryDependencyOpConf(), name="entry", group="dependency")
    store(CollectionDependencyOpConf(), name="collection", group="dependency")
    store(PipelineDependencyOpConf(), name="pipeline", group="dependency")
    store(GetPipelineFromApp(), name="get_app_service")
    store(ServiceIdConf(), name="service_id")
    store(just(PipelineConfig(), zen_convert=zc(dataclass=True)), name="pipeline_config")
