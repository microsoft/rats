from abc import abstractmethod
from typing import Protocol

import click


class CommandGroupPlugin(Protocol):
    @abstractmethod
    def on_group_open(self, group: click.Group) -> None:
        pass
