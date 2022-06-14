#!/usr/bin/env python3
import hydra
from hydra.core.config_store import ConfigStore
from hydra.utils import instantiate
from omegaconf import OmegaConf

from oneml.jzazo import schemata

cs = ConfigStore.instance()
schemata.register_configs(cs)


@hydra.main(config_path="conf", config_name="config")
def my_app(cfg: schemata.Config) -> None:
    print(OmegaConf.to_yaml(cfg))
    print(cfg.pipeline.stzlr.storage.namespace.name)
    print(instantiate(cfg.pipeline))


if __name__ == "__main__":
    my_app()
