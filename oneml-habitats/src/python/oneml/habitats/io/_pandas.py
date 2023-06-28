import pandas as pd

from oneml.io import IReadAndWriteData, LocalRWBase, RWDataUri


class PandasLocalRW(LocalRWBase, IReadAndWriteData[pd.DataFrame]):
    def write(self, data_uri: RWDataUri, payload: pd.DataFrame) -> None:
        path = self._get_path(data_uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload.to_parquet(path)

    def read(self, data_uri: RWDataUri) -> pd.DataFrame:
        path = self._get_path(data_uri)
        return pd.read_parquet(path)
