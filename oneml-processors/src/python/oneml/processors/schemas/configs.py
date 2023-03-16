from dataclasses import dataclass
from typing import Any

from hydra.core.config_store import ConfigStore

from ..ml import EstimatorConf
from ..ux import (
    CollectionDependencyOpConf,
    CombinedConf,
    EntryDependencyOpConf,
    IOCollectionDependencyOpConf,
    PipelineDependencyOpConf,
    TaskConf,
)


@dataclass
class Config:
    pipeline: Any = None


def register_configs(cs: ConfigStore) -> None:
    cs.store(group="task", name="base", node=TaskConf)
    cs.store(group="combined", name="base", node=CombinedConf)
    cs.store(group="estimator", name="base", node=EstimatorConf)
    cs.store(group="dependency", name="entry", node=EntryDependencyOpConf)
    cs.store(group="dependency", name="collection", node=CollectionDependencyOpConf)
    cs.store(group="dependency", name="collections", node=IOCollectionDependencyOpConf)
    cs.store(group="dependency", name="pipeline", node=PipelineDependencyOpConf)
    cs.store(name="config", node=Config)
