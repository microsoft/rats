from typing import Iterable

import click

from ._click import ClickCommandRegistry, command
from oneml.services import IExecutable, ServiceProvider


class OnemlDevtoolsCli(IExecutable):

    _registries_group_provider: ServiceProvider[Iterable[ClickCommandRegistry]]

    def __init__(self, registries_group_provider: ServiceProvider[Iterable[ClickCommandRegistry]]) -> None:
        self._registries_group_provider = registries_group_provider

    def execute(self) -> None:
        cli = click.Group()
        for registry in self._registries_group_provider():
            registry.register(cli)

        cli()


class OnemlDevtoolsCommands(ClickCommandRegistry):
    @command
    @click.argument("name")
    @click.option("--path")
    def hello(self, name: str, path: str) -> None:
        """say hello"""
        print(f"hello, {name} from {path}")

    @command
    @click.argument("name")
    @click.option("--reason", help="why you are saying goodbye?")
    def bye(self, name: str, reason: str) -> None:
        """say goodbye"""
        print(f"goodbye, {name} ({reason})")
