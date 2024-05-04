from collections.abc import Callable, Mapping
from typing import final

import click


class ClickCommandMapper:
    _commands: Mapping[str, Callable[[], click.Command]]

    def __init__(
        self,
        commands: Mapping[str, Callable[[], click.Command]],
    ) -> None:
        self._commands = commands

    def names(self) -> frozenset[str]:
        return frozenset(self._commands.keys())

    def get(self, name: str) -> click.Command:
        if name not in self._commands:
            raise ValueError(f"Command {name} not found")

        return self._commands[name]()


@final
class ClickCommandGroup(click.Group):
    _mapper: ClickCommandMapper

    def __init__(self, name: str, mapper: ClickCommandMapper) -> None:
        super().__init__(name=name)
        self._mapper = mapper

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return self._mapper.get(cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(self._mapper.names())
