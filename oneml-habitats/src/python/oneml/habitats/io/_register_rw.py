import numpy as np
import pandas as pd

from oneml.processors.io import IRegisterReadServiceForType, IRegisterWriteServiceForType

from ._services import OnemlHabitatsIoServices


class OnemlHabitatsRegisterReadersAndWriters:
    _readers_registry: IRegisterReadServiceForType
    _writers_registry: IRegisterWriteServiceForType

    def __init__(
        self,
        readers_registry: IRegisterReadServiceForType,
        writers_registry: IRegisterWriteServiceForType,
    ) -> None:
        self._readers_registry = readers_registry
        self._writers_registry = writers_registry

    def _register_numpy(self) -> None:
        def numpy_filter(t: type) -> bool:
            return issubclass(t, np.ndarray)

        self._readers_registry.register(
            "file", numpy_filter, OnemlHabitatsIoServices.NUMPY_LOCAL_READER
        )
        self._writers_registry.register(
            "file", numpy_filter, OnemlHabitatsIoServices.NUMPY_LOCAL_WRITER
        )

    def _register_pandas(self) -> None:
        def pandas_filter(t: type) -> bool:
            return issubclass(t, pd.DataFrame)

        self._readers_registry.register(
            "file", pandas_filter, OnemlHabitatsIoServices.PANDAS_LOCAL_READER
        )
        self._writers_registry.register(
            "file", pandas_filter, OnemlHabitatsIoServices.PANDAS_LOCAL_WRITER
        )

    def register(self) -> None:
        self._register_numpy()
        self._register_pandas()
