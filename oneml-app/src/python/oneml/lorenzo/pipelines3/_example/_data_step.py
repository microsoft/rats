import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Generic

from oneml.lorenzo.pipelines3 import (
    IExecutable,
    ILocateStorageItems,
    IProvideStorageItemKeys,
    IPublishStorageItems,
    OutputType,
    StorageItem,
    StorageItemKey,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExampleData:
    name: str
    value: str


class ExampleDataDataset(IProvideStorageItemKeys, Generic[OutputType]):
    _batch_id: int

    def __init__(self, batch_id: int):
        self._batch_id = batch_id

    def get(self) -> str:
        return f"repertoire.samples.batch-{self._batch_id}.parquet"


class DataProducerStep(IExecutable):
    _output: IPublishStorageItems

    def __init__(self, output: IPublishStorageItems):
        self._output = output

    def execute(self) -> None:
        logger.debug(f"Running DataProducerStep")
        # Saving output without a custom data id class
        output = StorageItem(
            key=StorageItemKey("example-data"),
            value=ExampleData(
                name="some-name",
                value="some-value"))
        self._output.publish_storage_item(output)

        # Or we can create a class for the dataset itself, for more structured naming.
        output = StorageItem(
            key=ExampleDataDataset(123),
            value=ExampleData(
                name="some-name",
                value="some-value"))

        self._output.publish_storage_item(output)


class DataConsumerStep(IExecutable):
    _data: ILocateStorageItems

    def __init__(self, data: ILocateStorageItems):
        self._data = data

    def execute(self) -> None:
        logger.debug(f"Running DataConsumerStep")
        # Reading without custom classes
        data1 = self._data.get_storage_item(StorageItemKey[ExampleData]("example-data"))
        logger.debug(data1)
        logger.debug(data1.value)

        # Reading with custom classes
        data2 = self._data.get_storage_item(ExampleDataDataset[ExampleData](123))
        logger.debug(data2)
        logger.debug(data2.value)
