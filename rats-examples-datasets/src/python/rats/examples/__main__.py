"""Run me with python -m rats.examples."""

from rats import apps
from rats import examples


def _run() -> None:
    app = apps.SimpleApplication(
        "rats.apps.plugins",
        "rats.examples",
    )
    app.execute(examples.PluginServices.MAIN_EXE)


if __name__ == "__main__":
    _run()
