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
    def _get_from_env(self) -> BlobStoreBaseLocation | None:
        account_name = os.environ.get("ONEML_HABITATS_DATASETS_BLOB_STORE_ACCOUNT")
        container_name = os.environ.get("ONEML_HABITATS_DATASETS_BLOB_STORE_CONTAINER")
        if account_name is None and container_name is not None:
            raise ValueError(
                "If you set ONEML_HABITATS_DATASETS_BLOB_STORE_CONTAINER, you must also set "
                + "ONEML_HABITATS_DATASETS_BLOB_STORE_ACCOUNT"
            )
        if account_name is not None and container_name is None:
            raise ValueError(
                "If you set ONEML_HABITATS_DATASETS_BLOB_STORE_ACCOUNT, you must also set "
                + "ONEML_HABITATS_DATASETS_BLOB_STORE_CONTAINER"
            )
        if account_name is not None and container_name is not None:
            return BlobStoreBaseLocation(
                account_name=account_name,
                container_name=container_name,
                base_path="oneml-datasets",
            )
        else:
            return None

    def _is_jupyter(self) -> bool:
        return "JPY_PARENT_PID" in os.environ

    def _is_production(self, namespace: str) -> bool:
        return namespace == "production"

    def get_blob_store_base_location(self, namespace: str) -> BlobStoreBaseLocation:
        from_env = self._get_from_env()
        if from_env is not None:
            return from_env
        if self._is_production(namespace):
            if self._is_jupyter():
                raise ValueError("Cannot use production namespace from Jupyter notebook")
            return BlobStoreBaseLocation(
                account_name="ampdatasets01",
                container_name="oneml-datasets",
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
                    container_name="oneml-datasets",
                    base_path="",
                )
