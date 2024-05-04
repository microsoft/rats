from collections.abc import Callable, Mapping

import click


class CommandProvider:
    _commands: Mapping[str, Callable[[], click.Command]]

    def __init__(
        self,
        commands: Mapping[str, Callable[[], click.Command]],
    ) -> None:
        self._commands = commands

    def list(self) -> frozenset[str]:
        return frozenset(self._commands.keys())

    def get(self, name: str) -> click.Command:
        if name not in self._commands:
            raise ValueError(f"Command {name} not found")

        return self._commands[name]()
