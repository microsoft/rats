from hydra.core.config_store import ConfigStore

from . import root, steps, storage
from .root import Config


def register_configs(cs: ConfigStore) -> None:
    steps.register_configs(cs)
    root.register_configs(cs)
    storage.register_configs(cs)


__all__ = ["Config"]
