import pytest

from oneml.habitats.pipeline_operations._datasets._blob_store_base_location_service import (
    BlobStoreBaseLocation,
    DatasetBlobStoreBaseLocationService,
)
from oneml.habitats.pipeline_operations._datasets._write_specifications import (
    DatasetWriteSpecifications,
)
from oneml.habitats.pipeline_operations._datasets._write_storage_location_service import (
    DatasetWriteStorageLocationService,
)


def test_get_blob_store_base_location() -> None:
    base_location_service = DatasetBlobStoreBaseLocationService()
    write_location_service = DatasetWriteStorageLocationService(
        blob_store_base_location_service=base_location_service
    )

    # Test production namespace
    location = base_location_service.get_blob_store_base_location("production")
    assert isinstance(location, BlobStoreBaseLocation)
    assert location.account_name == "ampdatasets01"
    assert location.container_name == "oneml-datasets"
    assert location.base_path == ""

    write_specifications = DatasetWriteSpecifications(
        name="test_ds",
        namespace="production",
        partition="test_partition",
        path_in_dataset="test_path",
        allow_overwrite=True,
    )
    uri = write_location_service.get_storage_uri(write_specifications)
    expected_start = (
        "abfss://oneml-datasets@ampdatasets01.dfs.core.windows.net/test_ds/test_partition/"
    )
    assert uri.startswith(expected_start)
    uuid = uri[len(expected_start) :]
    assert "/" not in uuid

    # Test non-production namespace
    location = base_location_service.get_blob_store_base_location("dev")
    assert isinstance(location, BlobStoreBaseLocation)
    assert location.account_name == "ampdatasetsdev01"
    assert location.container_name == "oneml-datasets"
    assert location.base_path == ""

    write_specifications = DatasetWriteSpecifications(
        name="test_ds",
        namespace="dev",
        partition="test_partition",
        path_in_dataset="test_path",
        allow_overwrite=True,
    )
    uri = write_location_service.get_storage_uri(write_specifications)
    expected_start = (
        "abfss://oneml-datasets@ampdatasetsdev01.dfs.core.windows.net/test_ds/test_partition/"
    )
    assert uri.startswith(expected_start)
    uuid = uri[len(expected_start) :]
    assert "/" not in uuid


def test_get_blob_store_base_location_with_jupyter_notebook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_location_service = DatasetBlobStoreBaseLocationService()
    write_location_service = DatasetWriteStorageLocationService(
        blob_store_base_location_service=base_location_service
    )

    with monkeypatch.context() as m:
        m.setenv("JPY_PARENT_PID", "1234")
        with pytest.raises(
            ValueError, match="Cannot use production namespace from Jupyter notebook"
        ):
            base_location_service.get_blob_store_base_location("production")

        # Test Jupyter notebook in non-production namespace
        location = base_location_service.get_blob_store_base_location("dev")
        assert isinstance(location, BlobStoreBaseLocation)
        assert location.account_name == "jupyterscratch01"
        assert location.container_name == "jupyterscratch01"
        assert location.base_path == "oneml_datasets"

        write_specifications = DatasetWriteSpecifications(
            name="test_ds",
            namespace="test_ns",
            partition="test_partition",
            path_in_dataset="test_path",
            allow_overwrite=True,
        )
        uri = write_location_service.get_storage_uri(write_specifications)
        expected_start = (
            "abfss://jupyterscratch01@jupyterscratch01.dfs.core.windows.net/oneml_datasets/test_ds/"
            "test_partition/"
        )
        assert uri.startswith(expected_start)
        uuid = uri[len(expected_start) :]
        assert "/" not in uuid


def test_get_blob_store_base_location_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_location_service = DatasetBlobStoreBaseLocationService()
    write_location_service = DatasetWriteStorageLocationService(
        blob_store_base_location_service=base_location_service
    )

    with monkeypatch.context() as m:
        m.setenv("JPY_PARENT_PID", "1234")
        m.setenv("ONEML_HABITATS_DATASETS_BLOB_STORE_ACCOUNT", "test_account")
        with pytest.raises(ValueError):
            base_location_service.get_blob_store_base_location("production")

    with monkeypatch.context() as m:
        m.setenv("JPY_PARENT_PID", "1234")
        m.setenv("ONEML_HABITATS_DATASETS_BLOB_STORE_CONTAINER", "test_container")
        with pytest.raises(ValueError):
            base_location_service.get_blob_store_base_location("production")

    with monkeypatch.context() as m:
        m.setenv("JPY_PARENT_PID", "1234")
        m.setenv("ONEML_HABITATS_DATASETS_BLOB_STORE_ACCOUNT", "test_account")
        m.setenv("ONEML_HABITATS_DATASETS_BLOB_STORE_CONTAINER", "test_container")

        # Test Jupyter notebook in non-production namespace
        location = base_location_service.get_blob_store_base_location("dev")
        assert isinstance(location, BlobStoreBaseLocation)
        assert location.account_name == "test_account"
        assert location.container_name == "test_container"
        assert location.base_path == "oneml-datasets"

        write_specifications = DatasetWriteSpecifications(
            name="test_ds",
            namespace="test_ns",
            partition="test_partition",
            path_in_dataset="ppp",
            allow_overwrite=True,
        )
        uri = write_location_service.get_storage_uri(write_specifications)
        expected_start = (
            "abfss://test_container@test_account.dfs.core.windows.net/oneml-datasets/test_ds/"
            "test_partition/"
        )
        assert uri.startswith(expected_start)
        uuid = uri[len(expected_start) :]
        assert "/" not in uuid
