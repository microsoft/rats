from typing import Tuple

from dataclasses import dataclass


@dataclass(frozen=True)
class RealsMatrix:
    data: Tuple[Tuple[float, ...], ...]
