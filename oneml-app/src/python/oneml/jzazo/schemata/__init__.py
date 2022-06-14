from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf

from . import root, steps, storage
from .root import Config

OmegaConf.register_new_resolver(
    "step_name", lambda _parent_: _parent_._get_full_key(None).split(".")[1]
)


def register_configs(cs: ConfigStore) -> None:
    steps.register_configs(cs)
    root.register_configs(cs)
    storage.register_configs(cs)


__all__ = ["Config"]
