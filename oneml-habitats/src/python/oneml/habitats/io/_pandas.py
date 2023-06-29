import logging

import pandas as pd

from oneml.io import IReadAndWriteData, LocalRWBase, RWDataUri

logger = logging.getLogger(__name__)


class PandasLocalRW(LocalRWBase, IReadAndWriteData[pd.DataFrame]):
    def write(self, data_uri: RWDataUri, payload: pd.DataFrame) -> None:
        logger.debug(f"{self.__class__.__name__}: writing to {data_uri}")
        path = self._get_path(data_uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload.to_parquet(path)

    def read(self, data_uri: RWDataUri) -> pd.DataFrame:
        logger.debug(f"{self.__class__.__name__}: reading from {data_uri}")
        path = self._get_path(data_uri)
        return pd.read_parquet(path)
