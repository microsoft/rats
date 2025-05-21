from dataclasses import dataclass


@dataclass(frozen=True)
class ExampleData:
    id: str
    thing_a: str
    thing_b: str
