import logging
import uuid

from dagster import asset, materialize

logger = logging.getLogger(__name__)


class Presenter:

    _results: list[str]

    def __init__(self) -> None:
        self._results = []

    def publish(self, thing: str) -> None:
        logger.warning(thing)
        self._results.append(thing)

    def get_latest(self) -> str:
        return self._results[-1]


class GenerateThings:

    _out: Presenter

    def __init__(self, out: Presenter) -> None:
        self._out = out

    def execute(self) -> None:
        self._out.publish(str(uuid.uuid4()))


class Adapter:

    _command: GenerateThings
    _presenter: Presenter

    def __init__(self, command: GenerateThings, presenter: Presenter) -> None:
        self._command = command
        self._presenter = presenter

    def generate_things(self) -> str:
        self._command.execute()
        return self._presenter.get_latest()


if __name__ == "__main__":
    data = Presenter()
    steps = GenerateThings(data)
    adapter = Adapter(steps, data)
    materialize([asset(adapter.generate_things)])
