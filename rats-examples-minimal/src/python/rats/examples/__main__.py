"""Run me with python -m rats.examples."""

from rats import apps


def _run() -> None:
    print("hello from the minimal world!")


app = apps.SimpleApplication(
    "rats.apps.plugins",
    "rats.examples.plugins",
)
app.execute_callable(_run)
