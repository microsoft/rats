from abc import abstractmethod
from typing import Protocol

from immunodata.datasets import Dataset, DatasetCommit, IDatasetConsumer

from ._read_specifications import DatasetReadSpecifications


class IDatasetReadCommitService(Protocol):
    @abstractmethod
    def get_commit(self, dataset: DatasetReadSpecifications) -> DatasetCommit:
        ...


class DatasetReadCommitService(IDatasetReadCommitService):
    _dataset_client: IDatasetConsumer

    def __init__(self, dataset_client: IDatasetConsumer) -> None:
        self._dataset_client = dataset_client

    def get_commit(self, dataset: DatasetReadSpecifications) -> DatasetCommit:
        if dataset.commit_id is None:
            partitions = self._dataset_client.get_partition_names(
                Dataset(name=dataset.name, namespace=dataset.namespace)
            )
            if not partitions:
                raise ValueError(
                    f"Dataset {dataset.name} in namespace {dataset.namespace} has no partitions."
                )
            if dataset.snapshot is not None:
                snapshot = dataset.snapshot
                partitions = list(filter(lambda p: p <= snapshot, partitions))
                if not partitions:
                    raise ValueError(
                        f"All partitions of dataset {dataset.name} in namespace "
                        f"{dataset.namespace} are after requested snapshot {dataset.snapshot}."
                    )
            if dataset.partition is not None:
                partition = dataset.partition
                partitions = list(filter(lambda p: p == partition, partitions))
                if not partitions:
                    raise ValueError(
                        f"Partition {dataset.partition} not found in dataset {dataset.name} in "
                        f"namespace {dataset.namespace}."
                    )
            partition = max(partitions)
            commit = self._dataset_client.get_commit(
                Dataset(name=dataset.name, namespace=dataset.namespace), partition
            )
            if commit is None:
                raise ValueError(
                    f"Couldnt find a commit for a partition reported to exist: {partition} for "
                    f"dataset {dataset.name} in namespace {dataset.namespace}."
                )
        else:
            commits = self._dataset_client.get_partitions(
                Dataset(name=dataset.name, namespace=dataset.namespace)
            ).partitions
            if not commits:
                raise ValueError(
                    f"Dataset {dataset.name} in namespace {dataset.namespace} has no commits"
                )
            commits = tuple(c for c in commits if c.id == dataset.commit_id)
            if not commits:
                raise ValueError(
                    f"Commit {dataset.commit_id} not found in dataset {dataset.name} in namespace "
                    f"{dataset.namespace}"
                )
            commit = commits[0]
        return commit
