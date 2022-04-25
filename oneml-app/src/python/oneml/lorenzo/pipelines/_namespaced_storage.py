from functools import lru_cache
from typing import Type

from ._pipeline_storage import PipelineStorage, DataType


class TypeNamespace:
    _name: str

    def __init__(self, name: str):
        self._name = name

    @lru_cache()
    def get_type(self, parent: Type) -> Type:
        return type(f"{self._name}.{parent.__name__}", (parent,), {})


class TypeNamespaceClient:

    @lru_cache()
    def get_namespace(self, name: str) -> TypeNamespace:
        return TypeNamespace(name=name)


class NamespacedStorage(PipelineStorage):

    _storage: PipelineStorage
    _namespace: TypeNamespace

    def __init__(self, storage: PipelineStorage, namespace: TypeNamespace):
        self._storage = storage
        self._namespace = namespace

    def save(self, key: Type[DataType], value: DataType) -> None:
        namespaced_key = self._namespace.get_type(key)
        self._storage.save(namespaced_key, value)  # type: ignore

    def load(self, key: Type[DataType]) -> DataType:
        return self._storage.load(self._namespace.get_type(key))  # type: ignore

# Can we make a class to save intermediate values built during a single step?
# self._storage.save(parameterized_data(DataFrame, "foo.bar"), df))?

# Can we make something similar to SQL transactions in order to undo/redo storage operations?
# Maybe checkpoints? How does this work with DAGs of data producers?

# Wrapping data in objects is a little more work
# item.data? maybe just getting better at naming these? item.data_pdf for pandas dataframes?

# How does this get used to name iterations in pipelines?
