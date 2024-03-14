from typing_extensions import NamedTuple


class SimpleMessage(NamedTuple):
    text: str


class SimpleMetrics(NamedTuple):
    prompt_complexity: float
