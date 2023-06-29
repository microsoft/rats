import logging
import uuid
from functools import lru_cache
from pathlib import Path

from azure.storage.blob import BlobClient
from furl import furl
from immunodata.blob import IBlobClientFactory

from oneml.io import DataType_co, DataType_contra, IReadData, IWriteData, RWDataUri

logger = logging.getLogger(__name__)


class BlobRWBase:
    _blob_client_factory: IBlobClientFactory

    def __init__(self, blob_client_factory: IBlobClientFactory) -> None:
        self._blob_client_factory = blob_client_factory

    @lru_cache
    def _parse_uri(self, data_uri: RWDataUri) -> tuple[str, str, str]:
        # abfss://CONTAINER_NAME@ACCOUNT.dfs.core.windows.net/BASE_PATH/
        split_uri = furl(data_uri.uri)
        if split_uri.scheme != "abfss":
            raise ValueError(f"Expected abfss scheme, got {split_uri.scheme}")
        if not split_uri.username:
            raise ValueError(
                f"Expected non-empty username part indicating blob container, got {split_uri.username}"
            )
        if not split_uri.host or not split_uri.host.endswith(".dfs.core.windows.net"):
            raise ValueError(f"Expected host ACCOUNT.dfs.core.windows.net, got {split_uri.host}")
        if not split_uri.path:
            raise ValueError(f"Expected non-empty path, got {split_uri.path}")
        if split_uri.query:
            raise ValueError(f"Expected empty query, got {split_uri.query}")
        if split_uri.fragment:
            raise ValueError(f"Expected empty fragment, got {split_uri.fragment}")

        container = split_uri.username
        storage_account = split_uri.host[: -len(".dfs.core.windows.net")]
        path = "/".join(split_uri.path.segments)
        return storage_account, container, path

    def _get_blob_client(self, data_uri: RWDataUri) -> BlobClient:
        storage_account, container, path = self._parse_uri(data_uri)
        container_client = self._blob_client_factory.get_container_client(
            storage_account, container
        )
        blob_client = container_client.get_blob_client(path)
        return blob_client


class BlobRWUsingLocalCacheBase(BlobRWBase):
    _local_cache_path: Path

    def __init__(
        self,
        blob_client_factory: IBlobClientFactory,
        local_cache_path: Path,
    ):
        super().__init__(blob_client_factory=blob_client_factory)
        self._local_cache_path = local_cache_path

    @lru_cache
    def _get_cache_path(self, data_uri: RWDataUri) -> Path:
        storage_account, container, path = self._parse_uri(data_uri)
        return self._local_cache_path / storage_account / container / path


class BlobReadUsingLocalCache(BlobRWUsingLocalCacheBase, IReadData[DataType_co]):
    _local_cache_path: Path
    _local_reader: IReadData[DataType_co]

    def __init__(
        self,
        blob_client_factory: IBlobClientFactory,
        local_cache_path: Path,
        local_reader: IReadData[DataType_co],
    ):
        super().__init__(
            blob_client_factory=blob_client_factory, local_cache_path=local_cache_path
        )
        self._local_reader = local_reader

    def _download(self, cache_path: Path, data_uri: RWDataUri) -> None:
        blob_client = self._get_blob_client(data_uri)
        downloader = blob_client.download_blob()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_destination = cache_path.parent / f"{uuid.uuid4()}"
        logger.debug(f"starting download to {tmp_destination}.")
        with tmp_destination.open("bw") as fle:
            downloader.readinto(fle)
        logger.debug(f"completed download to {tmp_destination}. renaming to {cache_path}.")
        tmp_destination.rename(cache_path)

    def read(self, data_uri: RWDataUri) -> DataType_co:
        logger.debug(f"{self.__class__.__name__}: reading from {data_uri}")
        cache_path = self._get_cache_path(data_uri)
        if not cache_path.exists():
            self._download(cache_path, data_uri)
        cache_uri = RWDataUri(cache_path.as_uri())
        return self._local_reader.read(cache_uri)


class BlobWriteUsingLocalCache(BlobRWUsingLocalCacheBase, IWriteData[DataType_contra]):
    _local_cache_path: Path
    _local_writer: IWriteData[DataType_contra]

    def __init__(
        self,
        blob_client_factory: IBlobClientFactory,
        local_cache_path: Path,
        local_writer: IWriteData[DataType_contra],
    ):
        super().__init__(
            blob_client_factory=blob_client_factory, local_cache_path=local_cache_path
        )
        self._local_writer = local_writer

    def _upload(self, cache_path: Path, data_uri: RWDataUri) -> None:
        blob_client = self._get_blob_client(data_uri)
        logger.debug(f"starting upload from {cache_path}.")
        with cache_path.open("br") as fle:
            blob_client.upload_blob(fle, overwrite=True)
        logger.debug(f"completed upload from {cache_path}.")

    def write(self, data_uri: RWDataUri, payload: DataType_contra) -> None:
        logger.debug(f"{self.__class__.__name__}: writing to {data_uri}")
        cache_path = self._get_cache_path(data_uri)
        self._local_writer.write(RWDataUri(cache_path.as_uri()), payload)
        self._upload(cache_path, data_uri)
