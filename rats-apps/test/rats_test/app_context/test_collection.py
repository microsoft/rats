from dataclasses import dataclass
from typing import Any

from rats import app_context, apps


@dataclass(frozen=True)
class ExampleConfig:
    name: str
    value: dict[str, str]


@apps.autoscope
class TestServices:
    CONTEXT_1 = apps.ServiceId[ExampleConfig]("context-1")


class TestCollection:
    _context: ExampleConfig
    _collection: app_context.Collection[Any]

    def setup_method(self) -> None:
        self._context = ExampleConfig("example1", {"a": "b"})
        self._collection = app_context.Collection[ExampleConfig].make(
            app_context.Context[ExampleConfig].make(TestServices.CONTEXT_1, self._context),
        )

    def test_basic_serialization(self) -> None:
        json_string = app_context.dumps(self._collection)
        print(json_string)
        loaded = app_context.loads(json_string)
        ctx = loaded.decoded_values(ExampleConfig, TestServices.CONTEXT_1)
        assert ctx[0] == self._context
