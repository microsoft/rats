import os
from abc import abstractmethod
from typing import NamedTuple, Protocol


class BlobStoreBaseLocation(NamedTuple):
    account_name: str
    container_name: str
    base_path: str


class IDatasetBlobStoreBaseLocationService(Protocol):
    @abstractmethod
    def get_blob_store_base_location(self, namespace: str) -> BlobStoreBaseLocation:
        ...


class DatasetBlobStoreBaseLocationService(IDatasetBlobStoreBaseLocationService):
    def _is_jupyter(self) -> bool:
        return "JPY_PARENT_PID" in os.environ

    def _is_production(self, namespace: str) -> bool:
        return namespace == "production"

    def get_blob_store_base_location(self, namespace: str) -> BlobStoreBaseLocation:
        if self._is_production(namespace):
            if self._is_jupyter():
                raise ValueError("Cannot use production namespace from Jupyter notebook")
            return BlobStoreBaseLocation(
                account_name="ampdatasets01",
                container_name="oneml_datasets",
                base_path="",
            )
        else:
            if self._is_jupyter():
                return BlobStoreBaseLocation(
                    account_name="jupyterscratch01",
                    container_name="jupyterscratch01",
                    base_path="oneml_datasets",
                )
            else:
                return BlobStoreBaseLocation(
                    account_name="ampdatasetsdev01",
                    container_name="oneml_datasets",
                    base_path="",
                )
