from collections.abc import Callable, Iterator
from functools import partial
from typing import Any, Protocol

import click

from rats import apps


def command(f: Callable[..., None]) -> Callable[..., None]:
    setattr(f, "__rats_is_command__", True)  # noqa: B010
    return f


class ClickCommandRegistry(Protocol):
    """Interface for classes that want to add `click` commands to a `click.Group`.

    The default implementation of `register` loops through all the methods in the class, looking
    for ones with the `__rats_is_command__` property, and adds them to the `click.Group`. The
    method name is used as the command name, and the docstring is used as the help text on the
    terminal.
    """

    def register(self, group: click.Group) -> None:
        """A sprinkling of introspection to allow class methods to be `click` commands.

        This default implementation loops through all the methods in the class and
        turns the ones with the `__rats_is_command__` property into `click` commands.
        The method name is used as the command name, and the docstring is used as the
        help text on the terminal.
        """

        def cb(_method_name: str, *args: Any, **kwargs: Any):
            """Callback handed to `click.Command`, calls the method with matching name on this class.

            When the command is decorated with `@click.params` and `@click.option`, `click` will
            call this callback with the parameters in the order they were defined. This callback
            then calls the method with the same name on this class, passing the parameters in
            reverse order. This is because the method is defined with the parameters in the
            reverse order to the decorator, so we need to reverse them again to get the correct
            order.
            """
            func = getattr(self, _method_name)
            func(*args, **kwargs)

        methods = [attr for attr in dir(self) if not attr.startswith("_")]
        for method_name in methods:
            method = getattr(self, method_name)
            if not getattr(method, "__rats_is_command__", False):
                continue

            params = list(reversed(getattr(method, "__click_params__", [])))

            group.add_command(
                click.Command(
                    name=method_name.lower().replace("_", "-").strip("-"),
                    callback=partial(cb, method_name),
                    short_help=method.__doc__,
                    params=params,
                )
            )


class ClickCommandGroup(apps.Executable):
    _registries: Callable[[], Iterator[ClickCommandRegistry]]

    def __init__(self, registries: Callable[[], Iterator[ClickCommandRegistry]]) -> None:
        self._registries = registries

    def execute(self) -> None:
        cli = click.Group()
        for registry in self._registries():
            registry.register(cli)

        cli()
