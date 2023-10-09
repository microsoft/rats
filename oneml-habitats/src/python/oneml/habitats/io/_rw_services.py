from typing import Any

import numpy.typing as npt
import pandas as pd

from oneml.io import IReadData, IWriteData
from oneml.services import ServiceId, scoped_service_ids


@scoped_service_ids
class OnemlHabitatsIoRwServices:
    NUMPY_LOCAL_READER = ServiceId[IReadData[npt.ArrayLike]]("numpy-local-rw")
    NUMPY_LOCAL_WRITER = ServiceId[IWriteData[npt.ArrayLike]]("numpy-local-rw")

    PANDAS_LOCAL_READER = ServiceId[IReadData[pd.DataFrame]]("pandas-local-rw")
    PANDAS_LOCAL_WRITER = ServiceId[IWriteData[pd.DataFrame]]("pandas-local-rw")

    NUMPY_BLOB_READER = ServiceId[IReadData[npt.ArrayLike]]("numpy-blob-reader")
    NUMPY_BLOB_WRITER = ServiceId[IWriteData[npt.ArrayLike]]("numpy-blob-writer")

    PANDAS_BLOB_READER = ServiceId[IReadData[pd.DataFrame]]("pandas-blob-reader")
    PANDAS_BLOB_WRITER = ServiceId[IWriteData[pd.DataFrame]]("pandas-blob-writer")
    DILL_BLOB_READER = ServiceId[IReadData[Any]]("dill-blob-reader")
    DILL_BLOB_WRITER = ServiceId[IWriteData[Any]]("dill-blob-writer")
    JSON_BLOB_READER = ServiceId[IReadData[Any]]("json-blob-reader")
    JSON_BLOB_WRITER = ServiceId[IWriteData[Any]]("json-blob-writer")
