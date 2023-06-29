import logging

import numpy as np
from numpy.typing import ArrayLike

from oneml.io import IReadAndWriteData, LocalRWBase, RWDataUri

logger = logging.getLogger(__name__)


class NumpyLocalRW(LocalRWBase, IReadAndWriteData[ArrayLike]):
    def write(self, data_uri: RWDataUri, payload: ArrayLike) -> None:
        logger.debug(f"{self.__class__.__name__}: writing to {data_uri}")
        path = self._get_path(data_uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            np.save(f, payload)

    def read(self, data_uri: RWDataUri) -> ArrayLike:
        logger.debug(f"{self.__class__.__name__}: reading from {data_uri}")
        path = self._get_path(data_uri)
        with path.open("rb") as f:
            return np.load(f)
