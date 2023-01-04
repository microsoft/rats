from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    name: str
    value: str
