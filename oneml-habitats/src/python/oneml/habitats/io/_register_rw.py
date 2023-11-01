import numpy as np
import pandas as pd

from oneml.processors.io import (
    IRegisterReadServiceForType,
    IRegisterWriteServiceForType,
    PluginRegisterReadersAndWriters,
)
from oneml.processors.pipeline_operations import Manifest

from ._rw_services import OnemlHabitatsIoRwServices


class OnemlHabitatsRegisterReadersAndWriters(PluginRegisterReadersAndWriters):
    def __init__(
        self,
        readers_registry: IRegisterReadServiceForType,
        writers_registry: IRegisterWriteServiceForType,
        oneml_processors_plugin: PluginRegisterReadersAndWriters,
    ) -> None:
        super().__init__(readers_registry, writers_registry, [oneml_processors_plugin])

    def _register(self) -> None:
        self._register_dill()
        self._register_numpy()
        self._register_pandas()

    def _register_numpy(self) -> None:
        def numpy_filter(t: type) -> bool:
            return issubclass(t, np.ndarray)

        self._readers_registry.register(
            "file", numpy_filter, OnemlHabitatsIoRwServices.NUMPY_LOCAL_READER
        )
        self._writers_registry.register(
            "file", numpy_filter, OnemlHabitatsIoRwServices.NUMPY_LOCAL_WRITER
        )
        self._readers_registry.register(
            "abfss", numpy_filter, OnemlHabitatsIoRwServices.NUMPY_BLOB_READER
        )
        self._writers_registry.register(
            "abfss", numpy_filter, OnemlHabitatsIoRwServices.NUMPY_BLOB_WRITER
        )

    def _register_pandas(self) -> None:
        def pandas_filter(t: type) -> bool:
            return issubclass(t, pd.DataFrame)

        self._readers_registry.register(
            "file", pandas_filter, OnemlHabitatsIoRwServices.PANDAS_LOCAL_READER
        )
        self._writers_registry.register(
            "file", pandas_filter, OnemlHabitatsIoRwServices.PANDAS_LOCAL_WRITER
        )
        self._readers_registry.register(
            "abfss", pandas_filter, OnemlHabitatsIoRwServices.PANDAS_BLOB_READER
        )
        self._writers_registry.register(
            "abfss", pandas_filter, OnemlHabitatsIoRwServices.PANDAS_BLOB_WRITER
        )

    def _register_dill(self) -> None:
        self._readers_registry.register(
            "abfss", lambda t: True, OnemlHabitatsIoRwServices.DILL_BLOB_READER
        )
        self._writers_registry.register(
            "abfss", lambda t: True, OnemlHabitatsIoRwServices.DILL_BLOB_WRITER
        )

    def _register_manifest(self) -> None:
        def type_filter(t: type) -> bool:
            if not isinstance(t, type):
                return False
            return issubclass(t, Manifest)

        self._readers_registry.register(
            "abfss", type_filter, OnemlHabitatsIoRwServices.JSON_BLOB_READER
        )
        self._writers_registry.register(
            "abfss", type_filter, OnemlHabitatsIoRwServices.JSON_BLOB_WRITER
        )
