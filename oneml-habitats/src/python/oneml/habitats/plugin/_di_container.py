import logging
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy.typing as npt
import pandas as pd
from immunodata.blob import IBlobClientFactory
from immunodata.core._immunocli import ImmunodataCoreContainer
from immunodata.immunocli.next import ImmunocliContainer

from oneml.app import OnemlAppServiceGroups
from oneml.io import DataType, IReadAndWriteData, IReadData, IWriteData, OnemlIoServices
from oneml.processors import OnemlProcessorsServices
from oneml.services import IProvideServices, group, provider

from ..io import (
    BlobReadUsingLocalCache,
    BlobWriteUsingLocalCache,
    NumpyLocalRW,
    OnemlHabitatsIoServices,
    PandasLocalRW,
)
from ..services import OnemlHabitatsServices
from ._register_rw import OnemlHabitatsRegisterReadersAndWriters

logger = logging.getLogger(__name__)


class OnemlHabitatsDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @provider(OnemlHabitatsIoServices.NUMPY_LOCAL_READER)
    @provider(OnemlHabitatsIoServices.NUMPY_LOCAL_WRITER)
    def numpy_local_rw(self) -> IReadAndWriteData[npt.ArrayLike]:
        return NumpyLocalRW()

    @provider(OnemlHabitatsIoServices.PANDAS_LOCAL_READER)
    @provider(OnemlHabitatsIoServices.PANDAS_LOCAL_WRITER)
    def pandas_local_rw(self) -> IReadAndWriteData[pd.DataFrame]:
        return PandasLocalRW()

    @provider(OnemlHabitatsIoServices.NUMPY_BLOB_READER)
    def numpy_blob_reader(self) -> IReadData[npt.ArrayLike]:
        return self._blob_reader_using_local_cache(
            self._app.get_service(OnemlHabitatsIoServices.NUMPY_LOCAL_READER)
        )

    @provider(OnemlHabitatsIoServices.NUMPY_BLOB_WRITER)
    def numpy_blob_writer(self) -> IWriteData[npt.ArrayLike]:
        return self._blob_writer_using_local_cache(
            self._app.get_service(OnemlHabitatsIoServices.NUMPY_LOCAL_WRITER)
        )

    @provider(OnemlHabitatsIoServices.PANDAS_BLOB_READER)
    def pandas_blob_reader(self) -> IReadData[pd.DataFrame]:
        return self._blob_reader_using_local_cache(
            self._app.get_service(OnemlHabitatsIoServices.PANDAS_LOCAL_READER)
        )

    @provider(OnemlHabitatsIoServices.PANDAS_BLOB_WRITER)
    def pandas_blob_writer(self) -> IWriteData[pd.DataFrame]:
        return self._blob_writer_using_local_cache(
            self._app.get_service(OnemlHabitatsIoServices.PANDAS_LOCAL_WRITER)
        )

    @provider(OnemlHabitatsIoServices.DILL_BLOB_READER)
    def dill_blob_reader(self) -> IReadData[Any]:
        return self._blob_reader_using_local_cache(
            self._app.get_service(OnemlIoServices.DILL_LOCAL_READER)
        )

    @provider(OnemlHabitatsIoServices.DILL_BLOB_WRITER)
    def dill_blob_writer(self) -> IWriteData[Any]:
        return self._blob_writer_using_local_cache(
            self._app.get_service(OnemlIoServices.DILL_LOCAL_WRITER)
        )

    def _blob_reader_using_local_cache(
        self, local_reader: IReadData[DataType]
    ) -> IReadData[DataType]:
        blob_client_factory = self._app.get_service(OnemlHabitatsServices.BLOB_CLIENT_FACTORY)
        local_cache_path = self._app.get_service(OnemlHabitatsServices.BLOB_CACHE_PATH)
        return BlobReadUsingLocalCache(
            blob_client_factory=blob_client_factory,
            local_cache_path=local_cache_path,
            local_reader=local_reader,
        )

    def _blob_writer_using_local_cache(
        self, local_writer: IWriteData[DataType]
    ) -> IWriteData[DataType]:
        blob_client_factory = self._app.get_service(OnemlHabitatsServices.BLOB_CLIENT_FACTORY)
        local_cache_path = self._app.get_service(OnemlHabitatsServices.BLOB_CACHE_PATH)
        return BlobWriteUsingLocalCache(
            blob_client_factory=blob_client_factory,
            local_cache_path=local_cache_path,
            local_writer=local_writer,
        )

    @provider(OnemlHabitatsServices.BLOB_CACHE_PATH)
    def blob_cache_path(self) -> Path:
        tmp_path = self._app.get_service(OnemlHabitatsServices.TMP_PATH)
        blob_cache_path = tmp_path / "blob_cache" / str(uuid.uuid4())
        blob_cache_path.mkdir(parents=True, exist_ok=True)
        return blob_cache_path

    @provider(OnemlHabitatsServices.TMP_PATH)
    def tmp_path(self) -> Path:
        locate_habitats_cli_di_containers = self._app.get_service(
            OnemlHabitatsServices.LOCATE_HABITATS_CLI_DI_CONTAINERS
        )
        cli_container = locate_habitats_cli_di_containers(ImmunocliContainer)
        project_config = cli_container.project_config()
        tmp_path = project_config.get_active_application_tmp_path()
        return tmp_path

    @group(OnemlAppServiceGroups.IO_REGISTRY_PLUGINS)
    @provider(OnemlHabitatsServices.PLUGIN_REGISTER_READERS_AND_WRITERS)
    @lru_cache
    def register_readers_and_writers(self) -> OnemlHabitatsRegisterReadersAndWriters:
        return OnemlHabitatsRegisterReadersAndWriters(
            readers_registry=self._app.get_service(OnemlProcessorsServices.REGISTER_TYPE_READER),
            writers_registry=self._app.get_service(OnemlProcessorsServices.REGISTER_TYPE_WRITER),
            oneml_processors_plugin=self._app.get_service(
                OnemlProcessorsServices.PLUGIN_REGISTER_READERS_AND_WRITERS
            ),
        )

    @provider(OnemlHabitatsServices.BLOB_CLIENT_FACTORY)
    def blob_client_factory(self) -> IBlobClientFactory:
        locate_habitats_cli_di_containers = self._app.get_service(
            OnemlHabitatsServices.LOCATE_HABITATS_CLI_DI_CONTAINERS
        )
        immunodata_core_di_container = locate_habitats_cli_di_containers(ImmunodataCoreContainer)
        blob_client_factory = immunodata_core_di_container.blob_client_factory()
        return blob_client_factory
