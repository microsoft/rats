import numpy.typing as npt
import pandas as pd

from oneml.io import IReadAndWriteData, IReadData, IWriteData
from oneml.services import ServiceId, scoped_service_ids


@scoped_service_ids
class OnemlHabitatsIoServices:
    NUMPY_LOCAL_READER = ServiceId[IReadData[npt.ArrayLike]]("numpy-local-rw")
    NUMPY_LOCAL_WRITER = ServiceId[IWriteData[npt.ArrayLike]]("numpy-local-rw")
    NUMPY_LOCAL_RW = ServiceId[IReadAndWriteData[npt.ArrayLike]]("numpy-local-rw")
    PANDAS_LOCAL_READER = ServiceId[IReadData[pd.DataFrame]]("pandas-local-rw")
    PANDAS_LOCAL_WRITER = ServiceId[IWriteData[pd.DataFrame]]("pandas-local-rw")
    PANDAS_LOCAL_RW = ServiceId[IReadAndWriteData[pd.DataFrame]]("pandas-local-rw")
