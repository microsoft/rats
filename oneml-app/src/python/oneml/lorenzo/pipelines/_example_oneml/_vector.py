from typing import Tuple

from dataclasses import dataclass


@dataclass(frozen=True)
class RealsVector:
    data: Tuple[float, ...]
