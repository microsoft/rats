"""..."""

import json
import logging
import os
import uuid
from collections.abc import Iterator

from rats import apps

logger = logging.getLogger(__name__)


class ExampleData:
    """A simple data source that might come from another package."""

    _num_samples: int

    def __init__(self, num_samples: int) -> None:
        """..."""
        self._num_samples = num_samples

    def fetch(self) -> Iterator[str]:
        """Yields random samples."""
        for i in range(self._num_samples):
            yield json.dumps({"index": i, "sample": str(uuid.uuid4())})


class ExampleExe(apps.Executable):
    """..."""

    _example_data: ExampleData

    def __init__(self, example_data: ExampleData) -> None:
        """..."""
        self._example_data = example_data

    def execute(self) -> None:
        """..."""
        for row in self._example_data.fetch():
            print(row)


@apps.autoscope
class PluginServices:
    """..."""

    MAIN_EXE = apps.ServiceId[apps.Executable]("main")
    EXAMPLE_DATA = apps.ServiceId[ExampleData]("example-data")


class PluginContainer(apps.Container):
    """..."""

    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        """..."""
        self._app = app

    @apps.service(PluginServices.MAIN_EXE)
    def _main_exe(self) -> apps.Executable:
        """..."""
        return ExampleExe(
            example_data=self._app.get(PluginServices.EXAMPLE_DATA),
        )

    @apps.service(PluginServices.EXAMPLE_DATA)
    def _example_data(self) -> ExampleData:
        """..."""
        return ExampleData(
            num_samples=int(os.environ.get("EXAMPLE_DATA_NUM_SAMPLES", "5")),
        )


if __name__ == "__main__":
    apps.SimpleApplication(runtime_plugin=PluginContainer).execute(
        PluginServices.MAIN_EXE,
    )
