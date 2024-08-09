"""..."""

import logging

import click

from rats import apps, cli

logger = logging.getLogger(__name__)


class ExampleCommands(cli.CommandContainer):
    """An example collection of cli commands."""

    @cli.command()
    @click.option("--exe-id", multiple=True)
    def _run_this(self, exe_id: tuple[str, ...]) -> None:
        """Example cli command called run-this."""
        print(f"running these exes: {exe_id}")

    @cli.command()
    @click.option("--exe-id", multiple=True)
    def _run_that(self, exe_id: tuple[str, ...]) -> None:
        """Example cli command called run-that."""
        print(f"running those exes: {exe_id}")

    @cli.group()
    def _run_these(self) -> None:
        """Example cli command called run-these."""
        print("running these sub-things")


@apps.autoscope
class ExampleServices:
    """
    Services used by the example container.

    These classes are global constants to identify the provided services.
    """

    MAIN = apps.ServiceId[apps.Executable]("main")


class ExampleContainer(apps.Container):
    """An example container of services."""

    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        """The root container allows us to access services in other plugins."""
        self._app = app

    @apps.service(ExampleServices.MAIN)
    def _main(self) -> apps.Executable:
        return cli.ClickApp(
            group=click.Group("example", help="An example application."),
            commands=ExampleCommands(),
        )


if __name__ == "__main__":
    apps.SimpleApplication(runtime_plugin=ExampleContainer).execute(
        ExampleServices.MAIN,
    )
