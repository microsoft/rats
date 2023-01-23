import logging
from abc import abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Protocol, cast

from azure.core.credentials import TokenCredential
from azure.storage.blob import BlobClient, BlobServiceClient

logger = logging.getLogger(__name__)


class IManageFiles(Protocol):
    @abstractmethod
    def read(self, path: str) -> bytes:
        pass

    @abstractmethod
    def write(self, path: str, data: bytes) -> None:
        pass


class LocalFilesystem(IManageFiles):

    _directory: Path

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def read(self, path: str) -> bytes:
        return (self._directory / path).read_bytes()

    def write(self, path: str, data: bytes) -> None:
        p = self._directory / path.lstrip("/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


class BlobFilesystem(IManageFiles):

    _credentials: TokenCredential
    _account: str
    _container: str

    def __init__(self, credentials: TokenCredential, account: str, container: str) -> None:
        self._credentials = credentials
        self._account = account
        self._container = container

    def read(self, path: str) -> bytes:
        logger.debug(f"reading data from {self._account}:{self._container}@{path}")
        return cast(bytes, self._get_blob_client(path).download_blob().readall())

    def write(self, path: str, data: bytes) -> None:
        logger.debug(f"writing data to {self._account}:{self._container}@{path}")
        self._get_blob_client(path).upload_blob(cast(Iterable[str], data))

    @lru_cache()
    def _get_blob_client(self, path: str) -> BlobClient:
        client_service = self._get_blob_service_client()
        return client_service.get_blob_client(self._container, path.lstrip("/"))

    @lru_cache()
    def _get_blob_service_client(self) -> BlobServiceClient:
        return BlobServiceClient(
            account_url=f"https://{self._account}.blob.core.windows.net/",
            credential=self._credentials,
        )
