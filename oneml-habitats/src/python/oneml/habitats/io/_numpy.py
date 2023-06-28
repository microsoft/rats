import numpy as np
from numpy.typing import ArrayLike

from oneml.io import IReadAndWriteData, LocalRWBase, RWDataUri


class NumpyLocalRW(LocalRWBase, IReadAndWriteData[ArrayLike]):
    def write(self, data_uri: RWDataUri, payload: ArrayLike) -> None:
        path = self._get_path(data_uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, payload)

    def read(self, data_uri: RWDataUri) -> ArrayLike:
        path = self._get_path(data_uri)
        return np.load(path)
