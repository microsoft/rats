from dataclasses import dataclass
from typing import Tuple, Dict


@dataclass(frozen=True)
class RawCliRequest:
    argv: Tuple[str, ...]
    environ: Dict[str, str]
