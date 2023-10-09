from datetime import datetime

import pytest
from immunodata.datasets import Dataset, DatasetCommit

from oneml.habitats.pipeline_operations._datasets._ampds_uri_service import (
    ComposeAmpdsUriFromCommit,
    DatasetReadSpecifications,
    DatasetWriteSpecifications,
    ParseAmpdsUriForRead,
    ParseAmpdsUriForWrite,
)


def test_parse_ampds_uri_for_read_with_partition() -> None:
    parser = ParseAmpdsUriForRead()
    uri = (
        "ampds://my-dataset/path/to/file?namespace=my-namespace&partition=2022-01-01&commit_id=123"
    )
    expected = DatasetReadSpecifications(
        name="my-dataset",
        namespace="my-namespace",
        partition="2022-01-01",
        snapshot=None,
        commit_id="123",
        path_in_dataset="/path/to/file",
    )
    assert parser(uri) == expected


def test_parse_ampds_uri_for_read_with_snapshot() -> None:
    parser = ParseAmpdsUriForRead()
    uri = "ampds://my-dataset/path/to/file?namespace=my-namespace&snapshot=2022-01-01"
    expected = DatasetReadSpecifications(
        name="my-dataset",
        namespace="my-namespace",
        partition=None,
        snapshot="2022-01-01",
        commit_id=None,
        path_in_dataset="/path/to/file",
    )
    assert parser(uri) == expected


def test_parse_ampds_uri_for_read_with_partition_and_snapshot() -> None:
    parser = ParseAmpdsUriForRead()
    uri = "ampds://my-dataset/path/to/file?namespace=my-namespace&partition=2022-01-01&snapshot=2022-01-01T00:00:00Z&commit_id=123"
    with pytest.raises(ValueError):
        parser(uri)


def test_parse_ampds_uri_for_write() -> None:
    parser = ParseAmpdsUriForWrite()
    uri = "ampds://my-dataset/path/to/file?namespace=my-namespace&partition=2022-01-01"
    expected = DatasetWriteSpecifications(
        name="my-dataset",
        namespace="my-namespace",
        partition="2022-01-01",
        allow_overwrite=False,
        path_in_dataset="/path/to/file",
    )
    assert parser(uri, allow_overwrite=False) == expected


def test_compose_ampds_uri_from_commit() -> None:
    dataset = Dataset(name="my-dataset", namespace="my-namespace")
    commit = DatasetCommit(
        dataset=dataset,
        partition="2022-01-01",
        id="123",
        uri="something",
        published_at=datetime.fromisoformat("2022-01-01T00:00:00"),
    )
    composer = ComposeAmpdsUriFromCommit()
    expected = "ampds://my-dataset?namespace=my-namespace&partition=2022-01-01&commit_id=123"
    assert composer(commit) == expected


def test_parse_ampds_uri_for_write_with_missing_namespace() -> None:
    parser = ParseAmpdsUriForWrite()
    uri = "ampds://my-dataset/path/to/file?partition=2022-01-01"
    with pytest.raises(ValueError):
        parser(uri, allow_overwrite=False)


def test_parse_ampds_uri_for_write_with_missing_partition() -> None:
    parser = ParseAmpdsUriForWrite()
    uri = "ampds://my-dataset/path/to/file?namespace=my-namespace"
    with pytest.raises(ValueError):
        parser(uri, allow_overwrite=False)
