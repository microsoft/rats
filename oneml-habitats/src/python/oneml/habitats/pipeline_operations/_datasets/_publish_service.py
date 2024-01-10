from abc import abstractmethod
from typing import Protocol

from immunodata.datasets import Dataset, DatasetCommit, IDatasetClient

from ._write_specifications import DatasetPublishSpecifications, DatasetWriteSpecifications


class IDatasetPublishService(Protocol):
    @abstractmethod
    def verify_ahead(self, dataset: DatasetWriteSpecifications) -> None:
        ...

    @abstractmethod
    def publish(self, dataset: DatasetPublishSpecifications) -> DatasetCommit:
        ...


class DatasetPublishService:
    _dataset_client: IDatasetClient

    def __init__(self, dataset_client: IDatasetClient) -> None:
        self._dataset_client = dataset_client

    def verify_ahead(self, dataset: DatasetWriteSpecifications) -> None:
        if not dataset.allow_overwrite:
            commit = self._dataset_client.get_commit(
                Dataset(name=dataset.name, namespace=dataset.namespace), dataset.partition
            )
            if commit is not None:
                raise ValueError(
                    f"Dataset {dataset.name} in namespace {dataset.namespace} was already "
                    + f"published for partition {dataset.partition}.  To overwrite, set "
                    + "allow_overwrite=True."
                )

    def publish(self, dataset: DatasetPublishSpecifications) -> DatasetCommit:
        commit = self._dataset_client.publish(
            dataset=Dataset(name=dataset.name, namespace=dataset.namespace),
            partition=dataset.partition,
            uri=dataset.storage_uri,
            parent_commits=dataset.parents,
        )
        return commit
