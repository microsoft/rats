import logging
from collections.abc import Callable
from functools import partial
from typing import Any, Protocol

import click

from ._annotations import get_class_commands

logger = logging.getLogger(__name__)


class CommandContainer(Protocol):
    """A container that can attach click commands to a click group."""

    def attach(self, group: click.Group) -> None:
        """..."""

        def cb(_method: Callable[..., None], *args: Any, **kwargs: Any) -> None:
            """
            Callback handed to `click.Command`. Calls the method with matching name on this class.

            When the command is decorated with `@click.params` and `@click.option`, `click` will
            call this callback with the parameters in the order they were defined. This callback
            then calls the method with the same name on this class, passing the parameters in
            reverse order. This is because the method is defined with the parameters in the
            reverse order to the decorator, so we need to reverse them again to get the correct
            order.
            """
            _method(*args, **kwargs)

        commands = get_class_commands(type(self))
        tates = commands.annotations

        for tate in tates:
            method = getattr(self, tate.name)
            params = list(reversed(getattr(method, "__click_params__", [])))
            logger.debug(tate.namespace)
            for command in tate.groups:
                if tate.namespace == "commands":
                    group.add_command(
                        click.Command(
                            name=command.name,
                            callback=partial(cb, method),
                            short_help=method.__doc__,
                            params=params,
                        )
                    )
