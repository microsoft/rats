import pytest

from oneml.habitats.pipeline_operations._datasets._blob_store_base_location_service import (
    BlobStoreBaseLocation,
    DatasetBlobStoreBaseLocationService,
)


def test_get_blob_store_base_location() -> None:
    service = DatasetBlobStoreBaseLocationService()

    # Test production namespace
    location = service.get_blob_store_base_location("production")
    assert isinstance(location, BlobStoreBaseLocation)
    assert location.account_name == "ampdatasets01"
    assert location.container_name == "oneml_datasets"
    assert location.base_path == ""

    # Test non-production namespace
    location = service.get_blob_store_base_location("dev")
    assert isinstance(location, BlobStoreBaseLocation)
    assert location.account_name == "ampdatasetsdev01"
    assert location.container_name == "oneml_datasets"
    assert location.base_path == ""


def test_get_blob_store_base_location_with_jupyter_notebook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = DatasetBlobStoreBaseLocationService()
    with monkeypatch.context() as m:
        m.setenv("JPY_PARENT_PID", "1234")
        with pytest.raises(
            ValueError, match="Cannot use production namespace from Jupyter notebook"
        ):
            service.get_blob_store_base_location("production")

        # Test Jupyter notebook in non-production namespace
        location = service.get_blob_store_base_location("dev")
        assert isinstance(location, BlobStoreBaseLocation)
        assert location.account_name == "jupyterscratch01"
        assert location.container_name == "jupyterscratch01"
        assert location.base_path == "oneml_datasets"
