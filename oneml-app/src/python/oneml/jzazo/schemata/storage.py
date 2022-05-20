from dataclasses import InitVar, dataclass
from typing import Any

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING


@dataclass
class InMemoryStorageConf:
    _target_: str = "oneml.lorenzo.pipelines._memory_storage.InMemoryStorage"


@dataclass
class TypeNamespaceConf:
    _target_: str = "oneml.lorenzo.pipelines._namespaced_storage.TypeNamespace"
    name: str = MISSING


@dataclass
class TypeNamespaceClientConf:
    _target_: str = "oneml.lorenzo.pipelines._namespaced_storage.TypeNamespaceClient"


@dataclass
class NamespacedStorageConf:
    _target_: str = "oneml.lorenzo.pipelines._namespaced_storage.NamespacedStorage"
    storage: Any = InMemoryStorageConf()
    namespace: Any = TypeNamespaceConf()


def register_configs(cs: ConfigStore) -> None:
    cs.store(group="storage", name="namespace", node=NamespacedStorageConf)
    cs.store(group="storage", name="namespace_client", node=TypeNamespaceClientConf)
