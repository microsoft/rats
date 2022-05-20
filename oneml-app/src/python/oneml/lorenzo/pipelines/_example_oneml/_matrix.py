from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class RealsMatrix:
    data: Tuple[Tuple[float, ...], ...]


@dataclass(frozen=True)
class RealsVector:
    data: Tuple[float, ...]
