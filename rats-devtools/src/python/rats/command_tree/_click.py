import functools
import itertools
import uuid
from collections.abc import Callable
from dataclasses import MISSING, dataclass, fields, is_dataclass
from typing import Annotated, Any, get_args, get_origin

import click
from click import Command, Group

from rats.apps import Executable

from ._command_tree import CommandTree
from ._docstring import get_attribute_docstring


@dataclass(frozen=True)
class ClickConversion:
    """Type annotations for the click conversion."""

    argument: bool = False
    """Whether the field is an argument."""

    explicit_click_type: click.ParamType | None = None
    """The explicit click type to use for the field."""


def to_click_commands(
    command: CommandTree,
    parent_kwarg_classes: tuple[type[Any], ...] = tuple(),
) -> Group | Command:
    """
    Recursively generate click commands and groups from the command tree.

    Traverse down the CommandTree until we hit a leaf node, collecting the argument groups along
    the way. Then, create a click command with the collected argument groups and the handler. Nodes
    traversed along the way are wrapped in a click group, and the click command is added to the
    group. Nested CommandTree handlers are expected to take the argument groups, in nesting order,
    as positional arguments.

    Args:
        command: The command tree to convert to click commands.
        parent_kwarg_classes: The dataclasses of the parent command arguments.

    Returns:
        A click group or command.
    """
    if command.kwargs_class is not None:
        parent_kwarg_classes = (*parent_kwarg_classes, command.kwargs_class)

    click_options_by_dataclass = {
        kwargs_class: dataclass_to_click_parameters(kwargs_class)
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
                    # We shouldn't be able to get here
                    # but just in case we do, we should raise an error
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
            raise ValueError(f"Command {command.name} has no handler")

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


def dataclass_to_click_parameters(
    dataclass: type[Any],
    parent_field_name: str | None = None,
    parent_nargs: int | None = None,
) -> tuple[click.Option, ...]:
    """
    Convert a dataclass to a list of click arguments.

    The dataclass fields are converted to click options, with the field name as the option name.
    If the field type is a tuple, the option is marked as multiple and the inner type is used.
    If the field type is a dataclass, the dataclass is recursively converted to click arguments.

    Args:
        dataclass: The dataclass to convert to click arguments.
        parent_field_name: The name of the parent field, if any.
        parent_nargs: The number of arguments for the parent field, if any.

    Returns:
        A tuple of click options.

    Raises:
        AssertionError: If the dataclass is not a dataclass.
    """
    assert is_dataclass(dataclass)

    parameters = []
    for field in fields(dataclass):
        option_name = field.name.replace("_", "-")
        if parent_field_name is not None:
            option_name = f"{parent_field_name}__{option_name}"

        if get_origin(field.type) is Annotated:
            base_field_type = get_args(field.type)[0]
            click_conversion_options = next(
                (
                    annotation
                    for annotation in get_args(field.type)
                    if isinstance(annotation, ClickConversion)
                ),
                ClickConversion(),
            )
        else:
            base_field_type = field.type
            click_conversion_options = ClickConversion()

        if get_origin(base_field_type) is tuple:
            inner_type = get_args(base_field_type)[0]

            if get_args(base_field_type) == (inner_type, ...):
                multiple = True
                nargs = -1
            else:
                multiple = False
                nargs = len(get_args(base_field_type))

            if is_dataclass(inner_type):
                parameters.extend(
                    dataclass_to_click_parameters(inner_type, option_name, parent_nargs=True)  # type: ignore
                )
                continue

            field_type = CLICK_TYPE_MAPPING[inner_type]
        else:
            if is_dataclass(base_field_type):
                parameters.extend(dataclass_to_click_parameters(base_field_type, option_name))  # type: ignore[reportArgumentType]
                continue

            field_type = CLICK_TYPE_MAPPING[base_field_type]
            if parent_nargs is not None:
                nargs = parent_nargs
                multiple = True
            else:
                nargs = 1
                multiple = False

        if click_conversion_options.explicit_click_type is not None:
            field_type = click_conversion_options.explicit_click_type

        required = field.default is MISSING and field.default_factory is MISSING
        help_str = get_attribute_docstring(dataclass, field.name)
        if click_conversion_options.argument:
            parameter = click.Argument(
                param_decls=[option_name],
                type=field_type,
                nargs=nargs,
                required=required,
            )
        else:
            parameter = click.Option(
                param_decls=[f"--{option_name}"],
                type=field_type,
                multiple=multiple,
                required=required,
                help=help_str,
            )
        parameters.append(parameter)

    return tuple(parameters)


class CommandTreeClickExecutable(Executable):
    def __init__(self, command_tree: CommandTree, standalone_mode: bool = True) -> None:
        self._command_tree = command_tree
        self._standalone_mode = standalone_mode

    def execute(self) -> None:
        cli = to_click_commands(self._command_tree)
        cli(standalone_mode=self._standalone_mode)
