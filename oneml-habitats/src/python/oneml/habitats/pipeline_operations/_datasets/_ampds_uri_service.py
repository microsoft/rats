from typing import Protocol
from urllib.parse import parse_qs, urlencode, urlparse, urlsplit, urlunparse

from immunodata.datasets import DatasetCommit

from ._read_specifications import DatasetReadSpecifications
from ._write_specifications import DatasetWriteSpecifications

# TODO: avoid repeating code in ParseAmpdsUriForRead and ParseAmpdsUriForWrite


class IParseAmpdsUriForRead(Protocol):
    def __call__(self, uri: str) -> DatasetReadSpecifications:
        ...


class ParseAmpdsUriForRead(IParseAmpdsUriForRead):
    def __call__(self, uri: str) -> DatasetReadSpecifications:
        def list_to_single_or_none(values: list[str], name: str) -> str | None:
            if len(values) > 1:
                raise ValueError(f"Found more than one value for {name} in query string")
            elif len(values) == 1:
                return values[0]
            else:
                return None

        parsed = urlsplit(uri)
        if parsed.scheme != "ampds":
            raise ValueError(f"Unexpected scheme found in URI: {uri}")
        dataset_name = parsed.netloc
        path_in_dataset = parsed.path
        parameters = parse_qs(parsed.query)

        def pop_parameter(parameter_name: str) -> str | None:
            values = parameters.pop(parameter_name, [])
            return list_to_single_or_none(values, parameter_name)

        namespace = pop_parameter("namespace") or "production"
        partition = pop_parameter("partition")
        snapshot = pop_parameter("snapshot")
        commit_id = pop_parameter("commit_id")
        if partition is not None and snapshot is not None:
            raise ValueError(
                f"Mutually exclusive parameters partition and snapshot found in URI {uri}"
            )
        if len(parameters) > 0:
            parameter_keys = ",".join(parameters.keys())
            raise ValueError(f"Unknown parameters {parameter_keys} found in URI {uri}")
        return DatasetReadSpecifications(
            name=dataset_name,
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
        def list_to_single_or_none(values: list[str], name: str) -> str | None:
            if len(values) > 1:
                raise ValueError(f"Found more than one value for {name} in query string")
            elif len(values) == 1:
                return values[0]
            else:
                return None

        parsed = urlsplit(uri)
        if parsed.scheme != "ampds":
            raise ValueError(f"Unexpected scheme found in URI: {uri}")
        dataset_name = parsed.netloc
        path_in_dataset = parsed.path
        parameters = parse_qs(parsed.query)

        def pop_parameter(parameter_name: str) -> str | None:
            values = parameters.pop(parameter_name, [])
            return list_to_single_or_none(values, parameter_name)

        namespace = pop_parameter("namespace")
        partition = pop_parameter("partition")

        if namespace is None:
            raise ValueError(f"Missing namespace in URI: {uri}")
        if partition is None:
            raise ValueError(f"Missing partition in URI: {uri}")
        return DatasetWriteSpecifications(
            name=dataset_name,
            namespace=namespace,
            partition=partition,
            allow_overwrite=allow_overwrite,
            path_in_dataset=path_in_dataset,
        )


class IComposeAmpdsUriFromReadSpecifications(Protocol):
    def __call__(self, read_specifications: DatasetReadSpecifications) -> str:
        ...


class ComposeAmpdsUriFromReadSpecifications(IComposeAmpdsUriFromReadSpecifications):
    def __call__(self, dataset_read_specifications: DatasetReadSpecifications) -> str:
        query_params_dict = {
            "namespace": dataset_read_specifications.namespace,
            "partition": dataset_read_specifications.partition,
            "snapshot": dataset_read_specifications.snapshot,
            "commit_id": dataset_read_specifications.commit_id,
        }
        query_params_dict = {k: v for k, v in query_params_dict.items() if v is not None}
        query_params = urlencode(query_params_dict)
        uri = urlunparse(
            (
                "ampds",
                dataset_read_specifications.name,
                dataset_read_specifications.path_in_dataset,
                "",
                query_params,
                "",
            )
        )
        return uri


class IComposeAmpdsUriFromCommit(Protocol):
    def __call__(self, commit: DatasetCommit) -> str:
        ...


class ComposeAmpdsUriFromCommit(IComposeAmpdsUriFromCommit):
    def __call__(self, commit: DatasetCommit) -> str:
        name = commit.dataset.name
        namespace = commit.dataset.namespace
        partition = commit.partition
        id = commit.id
        query_params = urlencode(
            {
                "namespace": namespace,
                "partition": partition,
                "commit_id": id,
            }
        )
        uri = urlunparse(("ampds", name, "", "", query_params, ""))
        return uri
