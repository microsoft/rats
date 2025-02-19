from collections.abc import Mapping
from dataclasses import dataclass


# TODO: it's not clear yet if this class belongs in `rats.apps`, `rats.cli`, or here.
#       currently placed here because it's only used in `rats.aml`.
@dataclass(frozen=True)
class Command:
    cwd: str
    args: tuple[str, ...]
    env: Mapping[str, str]
