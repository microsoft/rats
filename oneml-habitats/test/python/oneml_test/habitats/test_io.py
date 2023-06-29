from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from oneml.habitats.io import NumpyLocalRW, PandasLocalRW
from oneml.io import RWDataUri


def test_numpy(tmp_path: Path) -> None:
    rng = np.random.RandomState(2684432)
    f = tmp_path / "test.npy"
    uri = RWDataUri(f.as_uri())
    a = rng.randn(10)
    rw = NumpyLocalRW()
    rw.write(uri, a)
    b = rw.read(uri)
    assert np.array_equal(a, b)


def test_pandas(tmp_path: Path) -> None:
    rng = np.random.RandomState(2684432)
    f = tmp_path / "test.csv"
    uri = RWDataUri(f.as_uri())
    a = pd.DataFrame(
        dict(
            A=rng.randn(10),
            B=rng.randint(0, 10, 10),
            C=rng.randint(0, 10, 10),
            D=rng.choice(["a", "b", "c"], 10),
        )
    ).set_index(["D", "C"])
    rw = PandasLocalRW()
    rw.write(uri, a)
    b = rw.read(uri)
    assert pd.DataFrame.equals(a, b)
