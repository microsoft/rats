from abc import abstractmethod
from typing import Mapping, NamedTuple, Protocol

from furl import furl
from immunodata.datasets import ParentDatasetCommit

from ._ampds_uri_service import (
    IComposeAmpdsUriFromCommit,
    IParseAmpdsUriForRead,
    IParseAmpdsUriForWrite,
)
from ._publish_service import IDatasetPublishService
from ._read_commit_service import IDatasetReadCommitService
from ._write_specifications import DatasetPublishSpecifications
from ._write_storage_location_service import IDatasetWriteStorageLocationService


class DatasetPrepareOutput(NamedTuple):
    resolved_input_uris: Mapping[str, str]
    resolved_output_base_uri: str
    output_base_path_within_dataset: str | None
    dataset_publish_specifications: DatasetPublishSpecifications | None


class DatasetPublishOutput(NamedTuple):
    output_uris: Mapping[str, str]


class IDatasetPrepareAndPublishService(Protocol):
    @abstractmethod
    def prepare(
        self, input_uris: Mapping[str, str], output_base_uri: str, allow_overwrite: bool
    ) -> DatasetPrepareOutput:
        ...

    @abstractmethod
    def publish(
        self,
        resolved_output_base_uri: str,
        resolved_output_uris: Mapping[str, str],
        output_base_path_within_dataset: str | None,
        dataset_publish_specifications: DatasetPublishSpecifications | None,
    ) -> DatasetPublishOutput:
        ...


class DatasetPrepareAndPublishService:
    _parse_ampds_uri_for_read: IParseAmpdsUriForRead
    _parse_ampds_uri_for_write: IParseAmpdsUriForWrite
    _dataset_read_commit: IDatasetReadCommitService
    _dataset_write_storage_location: IDatasetWriteStorageLocationService
    _dataset_publish: IDatasetPublishService
    _compose_ampds_uri_from_commit: IComposeAmpdsUriFromCommit

    def __init__(
        self,
        parse_ampds_uri_for_read: IParseAmpdsUriForRead,
        parse_ampds_uri_for_write: IParseAmpdsUriForWrite,
        dataset_read_commit: IDatasetReadCommitService,
        dataset_write_storage_location: IDatasetWriteStorageLocationService,
        dataset_publish: IDatasetPublishService,
        compose_ampds_uri_from_commit: IComposeAmpdsUriFromCommit,
    ) -> None:
        self._parse_ampds_uri_for_read = parse_ampds_uri_for_read
        self._parse_ampds_uri_for_write = parse_ampds_uri_for_write
        self._dataset_read_commit = dataset_read_commit
        self._dataset_write_storage_location = dataset_write_storage_location
        self._dataset_publish = dataset_publish
        self._compose_ampds_uri_from_commit = compose_ampds_uri_from_commit

    def _parse_input_uri(self, input_uri: str) -> tuple[str, ParentDatasetCommit | None]:
        f = furl(input_uri)
        if f.scheme == "ampds":
            read_specification = self._parse_ampds_uri_for_read(input_uri)
            commit = self._dataset_read_commit.get_commit(read_specification)
            uri = str(furl(commit.uri) / read_specification.path_in_dataset)
            parent = commit.as_parent_dataset_commit()
        else:
            uri = input_uri
            parent = None
        return uri, parent

    def _parse_output_uri(
        self,
        output_uri: str,
        allow_overwrite: bool,
        parent_commits: tuple[ParentDatasetCommit, ...],
    ) -> tuple[str, str | None, DatasetPublishSpecifications | None]:
        f = furl(output_uri)
        if f.scheme == "ampds":
            write_specifications = self._parse_ampds_uri_for_write(output_uri, allow_overwrite)
            self._dataset_publish.verify_ahead(write_specifications)
            storage_uri = self._dataset_write_storage_location.get_storage_uri(
                write_specifications
            )
            uri = str(furl(storage_uri) / write_specifications.path_in_dataset)
            publish_specifications = DatasetPublishSpecifications(
                name=write_specifications.name,
                namespace=write_specifications.namespace,
                partition=write_specifications.partition,
                storage_uri=storage_uri,
                parents=parent_commits,
            )
            return uri, write_specifications.path_in_dataset, publish_specifications
        else:
            return output_uri, None, None

    def prepare(
        self, input_uris: Mapping[str, str], output_base_uri: str, allow_overwrite: bool
    ) -> DatasetPrepareOutput:
        parsed_inputs = {name: self._parse_input_uri(uri) for name, uri in input_uris.items()}
        resolved_input_uris = {name: uri for name, (uri, _) in parsed_inputs.items()}
        parent_commits = tuple(
            set(parent_commit for (_, parent_commit) in parsed_inputs.values() if parent_commit)
        )
        (
            resolved_output_base_uri,
            output_base_path_within_dataset,
            publish_specifications,
        ) = self._parse_output_uri(output_base_uri, allow_overwrite, parent_commits)
        return DatasetPrepareOutput(
            resolved_input_uris=resolved_input_uris,
            resolved_output_base_uri=resolved_output_base_uri,
            output_base_path_within_dataset=output_base_path_within_dataset,
            dataset_publish_specifications=publish_specifications,
        )

    def _get_relative_path(self, base_uri: str, target_uri: str) -> str:
        """Return the relative path of target_uri from base_uri"""
        base_parts = furl(base_uri)
        target_parts = furl(target_uri)

        base_path_segments = list[str](filter(None, base_parts.path.segments))
        target_path_segments = list[str](filter(None, target_parts.path.segments))

        base_parts = base_parts.copy().remove(path=True)
        target_parts = target_parts.copy().remove(path=True)

        # Check if the base and target URIs are identical up to the path component
        if base_parts != target_parts:
            raise ValueError(f"target URI {target_uri} is not a child of base URI {base_uri}")
        if base_path_segments != target_path_segments[: len(base_path_segments)]:
            raise ValueError(f"target URI {target_uri} is not a child of base URI {base_uri}")

        return "/".join(target_path_segments[len(base_path_segments) :])

    def publish(
        self,
        resolved_output_base_uri: str,
        resolved_output_uris: Mapping[str, str],
        output_base_path_within_dataset: str | None,
        dataset_publish_specifications: DatasetPublishSpecifications | None,
    ) -> DatasetPublishOutput:
        if dataset_publish_specifications is not None:
            commit = self._dataset_publish.publish(dataset_publish_specifications)
            dataset_uri = self._compose_ampds_uri_from_commit(commit)
            furi = furl(dataset_uri)
            relative_output_paths = {
                name: self._get_relative_path(resolved_output_base_uri, uri)
                for name, uri in resolved_output_uris.items()
            }
            output_uris: Mapping[str, str] = {
                name: str(furi / output_base_path_within_dataset / relative_path)
                for name, relative_path in relative_output_paths.items()
            }
        else:
            if output_base_path_within_dataset is not None:
                raise ValueError(
                    "output_base_path_within_dataset must be None if "
                    "dataset_publish_specifications is None"
                )
            output_uris = resolved_output_uris
        return DatasetPublishOutput(output_uris=output_uris)
