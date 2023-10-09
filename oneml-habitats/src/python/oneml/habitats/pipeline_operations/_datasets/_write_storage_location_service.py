from abc import abstractmethod
from typing import NamedTuple, Protocol
from uuid import uuid4

from furl import furl

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
        # abfss://CONTAINER_NAME@ACCOUNT.dfs.core.windows.net/PATH/
        uri = furl(
            scheme="abfss",
            username=blob_store_base_location.container_name,
            netloc=f"{blob_store_base_location.account_name}.dfs.core.windows.net",
            path=blob_store_base_location.base_path,
        )
        uri = uri / dataset.name / dataset.partition / uuid
        return uri.tostr()
