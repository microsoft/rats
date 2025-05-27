import logging
from collections.abc import Callable
from functools import partial
from typing import Any, Protocol, final

import click

from ._annotations import get_class_commands

logger = logging.getLogger(__name__)


class Container(Protocol):
    """
    A container that can attach click commands to a click group.

    !!! example
        The default protocol implementation detects any methods in the class decorated with the
        [rats.cli.command][] annotation. Apart from marking the method as a cli command, you can
        add [click.argument][] and [click.option][] decorators as defined by the click docs.

        ```python
        from rats import cli


        class ExampleCli(cli.Container):
            @cli.command()
            @click.argument("something")
            def my_cmd(self, something: str) -> None:
                print("this command is automatically detected and attached as my-cmd")
                print("add a docstring to the method to be used as the --help text")
        ```
    """

    def attach(self, group: click.Group) -> None:
        """
        Attach this container's provided cli commands to the provided [click.Group][].

        Args:
            group: The [click.Group][] we are attaching our commands to.
        """

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
        logger.debug(f"[{type(self)}] commands: {tates}")

        for tate in tates:
            method = getattr(self, tate.name)
            params = list(reversed(getattr(method, "__click_params__", [])))
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


@final
class CompositeContainer(Container):
    """Take any number of [rats.cli.Container][] instances and expose them as if they were one."""

    _containers: tuple[Container, ...]

    def __init__(self, *containers: Container) -> None:
        """
        Zero or more instances can be provided.

        Args:
            *containers: Any number of container instances wanting to be merged.
        """
        self._containers = containers

    def attach(self, group: click.Group) -> None:
        """
        Attach the cli commands from all [rats.cli.Container][] instances to the [click.Group][].

        Args:
            group: The [click.Group][] we are attaching our commands to.
        """
        for container in self._containers:
            container.attach(group)
