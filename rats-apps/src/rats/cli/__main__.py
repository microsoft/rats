"""..."""

import logging

import click

from rats import apps, cli

logger = logging.getLogger(__name__)


class ExampleCommands(cli.Container):
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


class ExampleContainer(apps.Container, apps.PluginMixin):
    """An example container of services."""

    def execute(self) -> None:
        """Run our ExampleCommands click group."""
        cli.create_group(
            group=click.Group("example", help="An example application."),
            container=ExampleCommands(),
        )()


if __name__ == "__main__":
    apps.run_plugin(ExampleContainer)
