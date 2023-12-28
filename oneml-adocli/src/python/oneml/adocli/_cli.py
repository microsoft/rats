from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class RawCliRequest:
    argv: Tuple[str, ...]
    environ: Dict[str, str]
