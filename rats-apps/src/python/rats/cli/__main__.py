from typing import final

import click

from rats import apps, cli


@final
class ClickApp(apps.Executable):
    _group: click.Group
    _commands: cli.CommandContainer

    def __init__(
        self,
        group: click.Group,
        commands: cli.CommandContainer,
    ) -> None:
        self._group = group
        self._commands = commands

    def execute(self) -> None:
        self._commands.on_group_open(self._group)
        self._group.main()


class ExampleCommands(cli.CommandContainer):
    @cli.command(cli.CommandId.auto())
    @click.option("--exe-id", multiple=True)
    def run_this(self, exe_id: tuple[str, ...]) -> None:
        print(f"running exes: {exe_id}")


@apps.autoscope
class ExampleServices:
    MAIN = apps.ServiceId[apps.Executable]("main")


class ExampleContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(ExampleServices.MAIN)
    def _main(self) -> apps.Executable:
        return ClickApp(
            group=click.Group("example", help="An example application."),
            commands=ExampleCommands(),
        )


if __name__ == "__main__":
    apps.SimpleApplication(runtime_plugin=ExampleContainer).execute(
        ExampleServices.MAIN,
    )
