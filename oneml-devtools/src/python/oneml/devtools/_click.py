from functools import partial

import click
from click import Command
from typing import Callable, Protocol


def command(f: Callable[[...], None]) -> Callable[[...], None]:
    f.__oneml_is_command__ = True
    return f


class ClickCommandRegistry(Protocol):

    def register(self, group: click.Group) -> None:
        """
        A sprinkling of introspection to allow class methods to be `click` commands.

        This default implementation loops through all the methods in the class and
        turns the ones with the `__oneml_is_command__` property into `click` commands.
        The method name is used as the command name, and the docstring is used as the
        help text on the terminal.
        """
        def cb(_name, *args, **kwargs):
            func = getattr(self, _name)
            func(*args, **kwargs)

        methods = [attr for attr in dir(self) if not attr.startswith("_")]
        for method_name in methods:
            method = getattr(self, method_name)
            if not getattr(method, "__oneml_is_command__", False):
                continue

            params = list(reversed(getattr(method, "__click_params__", [])))

            group.add_command(Command(
                name=method_name.lower().replace("_", "-").strip("-"),
                callback=partial(cb, method_name),
                help=method.__doc__,
                params=params,
            ))
