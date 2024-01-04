import os
from abc import abstractmethod
from typing import Protocol
from uuid import uuid4

from ._blob_store_base_location_service import IDatasetBlobStoreBaseLocationService
from ._write_specifications import DatasetWriteSpecifications


class IDatasetWriteStorageLocationService(Protocol):
    @abstractmethod
    def get_storage_uri(self, dataset: DatasetWriteSpecifications) -> str:
        ...


class DatasetWriteStorageLocationService(IDatasetWriteStorageLocationService):
    _blob_store_base_location_service: IDatasetBlobStoreBaseLocationService

    def __init__(
        self,
        blob_store_base_location_service: IDatasetBlobStoreBaseLocationService,
    ) -> None:
        self._blob_store_base_location_service = blob_store_base_location_service

    def get_storage_uri(self, dataset: DatasetWriteSpecifications) -> str:
        blob_store_base_location = (
            self._blob_store_base_location_service.get_blob_store_base_location(
                namespace=dataset.namespace
            )
        )
        uuid = str(uuid4())
        path = os.path.join(
            blob_store_base_location.base_path,
            dataset.name,
            dataset.partition,
            uuid,
        )
        # abfss://CONTAINER_NAME@ACCOUNT.dfs.core.windows.net/PATH/
        uri = (
            f"abfss://{blob_store_base_location.container_name}@"
            f"{blob_store_base_location.account_name}.dfs.core.windows.net/{path}"
        )
        return uri
