import pandas as pd

from oneml.io import IReadAndWriteData, RWDataUri


class PandasLocalRW(IReadAndWriteData[pd.DataFrame]):
    def write(self, data_uri: RWDataUri, payload: pd.DataFrame) -> None:
        payload.to_csv(data_uri.uri)

    def read(self, data_uri: RWDataUri) -> pd.DataFrame:
        return pd.read_csv(data_uri.uri)
