import numpy as np
from numpy.typing import ArrayLike

from oneml.io import IReadAndWriteData, RWDataUri


class NumpyLocalRW(IReadAndWriteData[ArrayLike]):
    def write(self, data_uri: RWDataUri, payload: ArrayLike) -> None:
        np.save(data_uri.uri, payload)

    def read(self, data_uri: RWDataUri) -> ArrayLike:
        return np.load(data_uri.uri)
