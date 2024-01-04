from typing import NamedTuple


class DatasetReadSpecifications(NamedTuple):
    name: str
    namespace: str
    path_in_dataset: str
    partition: str | None
    snapshot: str | None
    commit_id: str | None
