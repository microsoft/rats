from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import yaml

from ._config_service import IConfigService, T_ConfigType


class YamlFilePath(NamedTuple):
    yaml_file_path: str


class LoadYamlFromPathInContext(IConfigService):
    _yaml_path_provider: Callable[[], YamlFilePath]

    def __init__(self, yaml_path_provider: Callable[[], YamlFilePath]) -> None:
        self._yaml_path_provider = yaml_path_provider

    def __call__(self, config_type: type[T_ConfigType]) -> T_ConfigType:
        yaml_file_path = Path(self._yaml_path_provider().yaml_file_path)
        with yaml_file_path.open() as file:
            d = yaml.safe_load(file)
        if not isinstance(d, dict):
            raise ValueError(f"Expected a dictionary in {yaml_file_path}")
        return config_type(
            **d
        )  # TODO: type check, recursively convert fields that are dataclasses, etc.
