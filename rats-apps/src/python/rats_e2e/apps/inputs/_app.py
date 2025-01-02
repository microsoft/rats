import logging
from typing import NamedTuple
from uuid import uuid4

from rats import apps

logger = logging.getLogger(__name__)


class AppInput(NamedTuple):
    """A small data structure to provide the needed configuration for our application."""

    num_rows: int
    """The number of values we want printed by the [rats_e2e.apps.inputs.Application][] class."""


@apps.autoscope
class AppServices:
    INPUT = apps.ServiceId[AppInput]("input")


class Application(apps.AppContainer, apps.PluginMixin):
    """
    Prints a handful of random values to stdout.

    We can run this application with `apps.run_plugin(minimal.Application)` or directly in the
    terminal with `python -m rats_e2e.apps.inputs`. However, the library api allows the addition
    of a [rats.apps.Container][] with a service used as configuration.
    """

    def execute(self) -> None:
        """The main entry point to the application."""
        app_input = self._app.get(AppServices.INPUT)
        logger.info(f"running inputs application example with input: {app_input}")
        for _x in range(app_input.num_rows):
            print(uuid4())

    @apps.fallback_service(AppServices.INPUT)
    def _default_input(self) -> AppInput:
        # we can throw an exception if we want the input to be required without defaults
        logger.warning("default app input being used")
        return AppInput(5)


def main() -> None:
    apps.run_plugin(Application)
