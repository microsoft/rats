import functools
import itertools
import uuid
from collections.abc import Callable
from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin

import click
from click import Command, Group

from ._command_tree import CommandTree
from ._docstring import get_attribute_docstring


def to_click_commands(
    command: CommandTree,
    parent_kwarg_classes: tuple[type[Any], ...] = tuple(),
) -> Group | Command:
    """
    Recursively generate click commands and groups from the command tree.

    Traverse down the CommandTree until we hit a leaf node, collecting the argument groups along the way.
    Then, create a click command with the collected argument groups and the handler.
    Nodes traversed along the way are wrapped in a click group, and the click command is added to the group.
    Nested CommandTree handlers are expected to take the argument groups, in nesting order, as positional arguments.

    Args:
        command: The command tree to convert to click commands.
        parent_kwarg_classes: The dataclasses of the parent command arguments.

    Returns:
        A click group or command.
    """
    if command.kwargs_class is not None:
        parent_kwarg_classes = (*parent_kwarg_classes, command.kwargs_class)

    click_options_by_dataclass = {
        kwargs_class: dataclass_to_click_arguments(kwargs_class)
        for kwargs_class in parent_kwarg_classes
    }

    command_wrapper: Callable[..., None] | None
    if command.handler is not None:

        @functools.wraps(command.handler)
        def wrapper_func(**kwargs: Any):
            handler_args = []
            for kwargs_class, click_options in click_options_by_dataclass.items():
                kwargs_class_init = {}
                for option in click_options:
                    # We shouldn't be able to get here, but just in case we do, we should raise an error
                    if option.name is None:
                        raise ValueError("Option name cannot be None")

                    kwargs_class_init[option.name] = kwargs[option.name]

                handler_args.append(kwargs_class(**kwargs_class_init))

            assert command.handler is not None
            command.handler(*handler_args)

        command_wrapper = wrapper_func
    else:
        command_wrapper = None

    # if we're on a leaf node, we need to generate a click command
    if not command.children:
        if command.handler is None:
            raise ValueError("Command has no handler")

        return Command(
            name=command.name,
            help=command.description,
            params=list(itertools.chain.from_iterable(click_options_by_dataclass.values())),
            callback=command_wrapper,
        )
    else:
        # if we're not on a leaf node, we need to generate a click group
        group_to_add = Group(name=command.name, help=command.description, callback=command_wrapper)
        for child in command.children:
            group_to_add.add_command(to_click_commands(child, parent_kwarg_classes))

        return group_to_add


CLICK_TYPE_MAPPING = {
    int: click.INT,
    float: click.FLOAT,
    str: click.STRING,
    bool: click.BOOL,
    uuid.UUID: click.UUID,
}


def dataclass_to_click_arguments(
    dataclass: type[Any], parent_field_name: str | None = None, parent_is_multiple: bool = False
) -> tuple[click.Option, ...]:
    """
    Convert a dataclass to a list of click arguments.

    The dataclass fields are converted to click options, with the field name as the option name.
    If the field type is a tuple, the option is marked as multiple and the inner type is used.
    If the field type is a dataclass, the dataclass is recursively converted to click arguments.

    Args:
        dataclass: The dataclass to convert to click arguments.
        parent_field_name: The name of the parent field, if any.
        parent_is_multiple: Whether the parent field is multiple.

    Returns:
        A tuple of click options.

    Raises:
        AssertionError: If the dataclass is not a dataclass.
    """
    assert is_dataclass(dataclass)

    arguments = []
    for field in fields(dataclass):
        if get_origin(field.type) is tuple:
            inner_type = get_args(field.type)[0]

            if is_dataclass(inner_type):
                arguments.extend(
                    dataclass_to_click_arguments(inner_type, field.name, parent_is_multiple=True)
                )
                continue

            field_type = CLICK_TYPE_MAPPING[inner_type]
            multiple = True
        else:
            if is_dataclass(field.type):
                arguments.extend(dataclass_to_click_arguments(field.type, field.name))
                continue

            field_type = CLICK_TYPE_MAPPING[field.type]
            multiple = parent_is_multiple

        if parent_field_name is not None:
            param_decls = [f"--{parent_field_name}__{field.name}"]
        else:
            param_decls = [f"--{field.name}"]

        arguments.append(
            click.Option(
                param_decls=param_decls,
                type=field_type,
                multiple=multiple,
                help=get_attribute_docstring(dataclass, field.name),
            )
        )

    return tuple(arguments)
