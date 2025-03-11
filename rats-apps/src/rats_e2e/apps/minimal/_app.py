import logging
import os
from uuid import uuid4

from rats import apps

logger = logging.getLogger(__name__)


class Application(apps.AppContainer, apps.PluginMixin):
    """
    Prints a handful of random values to stdout.

    We can run this application with `apps.run_plugin(minimal.Application)` or directly in the
    terminal with `python -m rats_e2e.apps.minimal`. Use the `RATS_E2E_NUM_VALUES` environment
    variable to alter the number of values to print.
    """

    def execute(self) -> None:
        """The main entry point to the application."""
        logger.info("running minimal application example")
        for _x in range(int(os.environ.get("RATS_E2E_NUM_VALUES", 5))):
            print(uuid4())


def main() -> None:
    """Entry point function to register this application as a script."""
    apps.run_plugin(Application)
