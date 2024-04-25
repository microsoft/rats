from dataclasses import dataclass, field
from typing import Any

from hydra_zen import ZenStore, hydrated_dataclass, just
from hydra_zen.typing import ZenConvert as zc
from omegaconf import MISSING

from rats.processors._legacy_subpackages.registry import IProvidePipelineCollection
from rats.services import ServiceId

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


def get_pipeline(key: str, pipeline_providers: IProvidePipelineCollection) -> UPipeline:
    pipeline_provider = pipeline_providers[key]
    return pipeline_provider()


@hydrated_dataclass(get_pipeline)
class GetPipelineFromProvider:
    key: str = MISSING
    pipeline_providers: Any = "${pipeline_providers}"


@dataclass
class PipelineConfig:
    configs: dict[str, Any] = field(default_factory=dict)
    service_ids: dict[str, ServiceIdConf] = field(default_factory=dict)
    pipeline_providers: Any = MISSING
    pipeline: Any = None


def register_configs(store: ZenStore) -> None:
    store(TaskConf(), name="base", group="task")
    store(CombinedConf(), name="base", group="combined")
    store(EstimatorConf(), name="base", group="estimator")
    store(DuplicatePipelineConf(), name="base", group="duplicate")
    store(EntryDependencyOpConf(), name="entry", group="dependency")
    store(CollectionDependencyOpConf(), name="collection", group="dependency")
    store(PipelineDependencyOpConf(), name="pipeline", group="dependency")
    store(GetPipelineFromProvider(), name="get_pipeline")
    store(ServiceIdConf(), name="service_id")
    store(just(PipelineConfig(), zen_convert=zc(dataclass=True)), name="pipeline_config")
