from typing import NamedTuple

from immunodata.datasets import ParentDatasetCommit


class DatasetWriteSpecifications(NamedTuple):
    name: str
    namespace: str
    partition: str
    allow_overwrite: bool
    path_in_dataset: str


class DatasetPublishSpecifications(NamedTuple):
    name: str
    namespace: str
    partition: str
    storage_uri: str
    parents: tuple[ParentDatasetCommit, ...]
