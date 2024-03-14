from dataclasses import dataclass


@dataclass(frozen=True)
class RawCliRequest:
    argv: tuple[str, ...]
    environ: dict[str, str]
