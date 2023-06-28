import logging
from pathlib import Path

import numpy.typing as npt
import pandas as pd
from immunodata.immunocli.next import ImmunocliContainer

from oneml.io import IReadAndWriteData
from oneml.processors import OnemlProcessorsServices
from oneml.services import IProvideServices, provider

from ..io import (
    NumpyLocalRW,
    OnemlHabitatsIoServices,
    OnemlHabitatsRegisterReadersAndWriters,
    PandasLocalRW,
)
from ..services import OnemlHabitatsServices

logger = logging.getLogger(__name__)


class OnemlHabitatsDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @provider(OnemlHabitatsIoServices.NUMPY_LOCAL_RW)
    def numpy_local_rw(self) -> IReadAndWriteData[npt.ArrayLike]:
        return NumpyLocalRW()

    @provider(OnemlHabitatsIoServices.PANDAS_LOCAL_RW)
    def pandas_local_rw(self) -> IReadAndWriteData[pd.DataFrame]:
        return PandasLocalRW()

    @provider(OnemlHabitatsServices.TMP_PATH)
    def tmp_path(self) -> Path:
        locate_habitats_cli_di_containers = self._app.get_service(
            OnemlHabitatsServices.LOCATE_HABITATS_CLI_DI_CONTAINERS
        )
        cli_container = locate_habitats_cli_di_containers(ImmunocliContainer)
        project_config = cli_container.project_config()
        tmp_path = project_config.get_active_application_tmp_path()
        return tmp_path

    def _register_readers_and_writers(self) -> OnemlHabitatsRegisterReadersAndWriters:
        return OnemlHabitatsRegisterReadersAndWriters(
            readers_registry=self._app.get_service(OnemlProcessorsServices.REGISTER_TYPE_READER),
            writers_registry=self._app.get_service(OnemlProcessorsServices.REGISTER_TYPE_WRITER),
        )
