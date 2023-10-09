from typing import Protocol

from furl import furl
from immunodata.datasets import DatasetCommit

from ._read_specifications import DatasetReadSpecifications
from ._write_specifications import DatasetWriteSpecifications


class IParseAmpdsUriForRead(Protocol):
    def __call__(self, uri: str) -> DatasetReadSpecifications:
        ...


class ParseAmpdsUriForRead(IParseAmpdsUriForRead):
    def __call__(self, uri: str) -> DatasetReadSpecifications:
        furi = furl(uri)
        if furi.scheme != "ampds":
            raise ValueError(f"Unexpected scheme found in URI: {uri}")
        name = furi.netloc
        path_in_dataset = str(furi.path)
        namespace = furi.query.params.get("namespace", None)
        partition = furi.query.params.get("partition", None)
        snapshot = furi.query.params.get("snapshot", None)
        commit_id = furi.query.params.get("commit_id", None)
        if partition is not None and snapshot is not None:
            raise ValueError(
                f"Mutually exclusive parameters partition and snapshot found in URI: {uri}"
            )
        return DatasetReadSpecifications(
            name=name,
            namespace=namespace,
            partition=partition,
            snapshot=snapshot,
            commit_id=commit_id,
            path_in_dataset=path_in_dataset,
        )


class IParseAmpdsUriForWrite(Protocol):
    def __call__(self, uri: str, allow_overwrite: bool) -> DatasetWriteSpecifications:
        ...


class ParseAmpdsUriForWrite(IParseAmpdsUriForWrite):
    def __call__(self, uri: str, allow_overwrite: bool) -> DatasetWriteSpecifications:
        furi = furl(uri)
        if furi.scheme != "ampds":
            raise ValueError(f"Unexpected scheme found in URI: {uri}")
        name = furi.netloc
        path_in_dataset = str(furi.path)
        try:
            namespace = furi.query.params["namespace"]
        except KeyError:
            raise ValueError(f"Missing namespace in URI: {uri}")
        try:
            partition = furi.query.params["partition"]
        except KeyError:
            raise ValueError(f"Missing partition in URI: {uri}")
        return DatasetWriteSpecifications(
            name=name,
            namespace=namespace,
            partition=partition,
            allow_overwrite=allow_overwrite,
            path_in_dataset=path_in_dataset,
        )


class IComposeAmpdsUriFromCommit(Protocol):
    def __call__(self, commit: DatasetCommit) -> str:
        ...


class ComposeAmpdsUriFromCommit(IComposeAmpdsUriFromCommit):
    def __call__(self, commit: DatasetCommit) -> str:
        name = commit.dataset.name
        namespace = commit.dataset.namespace
        partition = commit.partition
        id = commit.id
        uri = furl(
            scheme="ampds",
            netloc=name,
            query_params={
                "namespace": namespace,
                "partition": partition,
                "commit_id": id,
            },
        )
        return uri.tostr()
