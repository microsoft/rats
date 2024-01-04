import re
from uuid import uuid4

import pytest
from immunodata.datasets import DatasetClient, IDatasetClient
from immunodata.datasets.storage import DatasetMemoryStorage

from oneml.habitats.pipeline_operations._datasets._publish_service import DatasetPublishService
from oneml.habitats.pipeline_operations._datasets._write_specifications import (
    DatasetPublishSpecifications,
    DatasetWriteSpecifications,
)
from oneml.habitats.pipeline_operations._datasets._write_storage_location_service import (
    IDatasetWriteStorageLocationService,
)


class MockDatasetWriteStorageLocationService(IDatasetWriteStorageLocationService):
    def get_storage_uri(self, dataset: DatasetWriteSpecifications) -> str:
        uuid = str(uuid4())
        return f"mock_storage://{dataset.name}/{dataset.namespace}/{dataset.partition}/{uuid}"


@pytest.fixture
def write_storage_location_service() -> IDatasetWriteStorageLocationService:
    return MockDatasetWriteStorageLocationService()


@pytest.fixture
def dataset_client() -> IDatasetClient:
    return DatasetClient(DatasetMemoryStorage())


def test_publish_from_write_specifications(
    dataset_client: IDatasetClient,
    write_storage_location_service: IDatasetWriteStorageLocationService,
) -> None:
    publish_service = DatasetPublishService(dataset_client)
    write_specifications = DatasetWriteSpecifications(
        name="test_dataset",
        namespace="test_namespace",
        partition="2022-01-01",
        path_in_dataset="test_path",
        allow_overwrite=True,
    )
    publish_specifications = DatasetPublishSpecifications(
        name="test_dataset",
        namespace="test_namespace",
        partition="2022-01-01",
        storage_uri=write_storage_location_service.get_storage_uri(write_specifications),
        parents=tuple(),
    )
    commit = publish_service.publish(publish_specifications)
    assert commit.dataset_name == "test_dataset"
    assert commit.dataset_namespace == "test_namespace"
    assert commit.partition == "2022-01-01"
    assert commit.id is not None
    assert re.match("^mock_storage://test_dataset/test_namespace/2022-01-01/[^/]+$", commit.uri)
