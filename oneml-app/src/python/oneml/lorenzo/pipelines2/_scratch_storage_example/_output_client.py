from typing import Type

from oneml.lorenzo.pipelines import InMemoryStorage

from ._pipeline_output import OutputType, PipelineOutput
from ._writers import LocalStorage


class MyPipelineOutput(PipelineOutput):

    _memory_storage: InMemoryStorage
    _local_storage: LocalStorage

    def __init__(self, memory_storage: InMemoryStorage, local_storage: LocalStorage):
        self._memory_storage = memory_storage
        self._local_storage = local_storage

    def add(self, name: Type[OutputType], value: OutputType) -> None:
        print(f"ADDING OUTPUT: {name}")
        self._memory_storage.save(name, value)
        self._local_storage.save(name, value)
