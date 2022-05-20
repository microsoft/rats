from dataclasses import dataclass
from typing import Any

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING


@dataclass
class Config:
    pipeline: Any = MISSING
    tasks: Any = MISSING
    io: Any = MISSING


def register_configs(cs: ConfigStore) -> None:
    cs.store(name="base_config", node=Config)
