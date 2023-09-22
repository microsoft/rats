from typing import NamedTuple


class SimpleMessage(NamedTuple):
    text: str


class SimpleMetrics(NamedTuple):
    prompt_complexity: float
