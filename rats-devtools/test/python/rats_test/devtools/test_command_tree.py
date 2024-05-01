from dataclasses import dataclass
from typing import Any
from typing import Any, Tuple

import click
import pytest

from rats.devtools._command_tree import (
    CommandTree,
    dataclass_to_click_arguments,
    get_attribute_docstring,
)

@dataclass
class MockNestedTupleArguments:
    """MockNestedTupleArguments description."""

    arg1: Tuple[MockArguments, ...]
    """A tuple of MockArguments."""

def test_dataclass_to_click_arguments_nested_tuple():
    arguments = dataclass_to_click_arguments(MockNestedTupleArguments)
    assert len(arguments) == 2, "There should be two click arguments for the nested tuple field."
    assert arguments[0].name == "arg1__arg1", "The nested tuple first argument name should be 'arg1__arg1'."
    assert arguments[1].name == "arg1__arg2", "The nested tuple second argument name should be 'arg1__arg2'."
    assert isinstance(arguments[0].type, click.types.Tuple), "The nested tuple first argument should be of type click.types.Tuple."
    assert isinstance(arguments[1].type, click.types.Tuple), "The nested tuple second argument should be of type click.types.Tuple."
    assert arguments[0].multiple is True, "The nested tuple first argument should have 'multiple' set to True."
    assert arguments[1].multiple is True, "The nested tuple second argument should have 'multiple' set to True."

@dataclass
class MockTupleArguments:
    """MockTupleArguments description."""

    arg1: Tuple[int, ...]
    """A tuple argument."""

def test_dataclass_to_click_arguments_tuple():
    arguments = dataclass_to_click_arguments(MockTupleArguments)
    assert len(arguments) == 1, "There should be one click argument for the tuple field."
    assert arguments[0].name == "arg1", "The tuple argument name should be 'arg1'."
    assert isinstance(arguments[0].type, click.types.Tuple), "The tuple argument should be of type click.types.Tuple."
    assert arguments[0].multiple is True, "The tuple argument should have 'multiple' set to True."


class ProgrammaticExecutionGroup(click.Group):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Alias for :meth:`main`."""
        return self.main(*args, standalone_mode=False, **kwargs)


@dataclass
class MockArguments:
    """MockArguments description."""

    arg1: str
    """The first argument."""

    arg2: int
    """The second argument."""


@dataclass
class NestedMockArguments:
    """NestedMockArguments description."""

    nested_arg: MockArguments
    """Nested argument dataclass."""


def test_dataclass_to_click_arguments_flat():
    arguments = dataclass_to_click_arguments(MockArguments)
    assert len(arguments) == 2, "There should be two click arguments."
    assert arguments[0].name == "arg1", "The first argument name should be 'arg1'."
    assert arguments[1].name == "arg2", "The second argument name should be 'arg2'."


def test_dataclass_to_click_arguments_nested():
    arguments = dataclass_to_click_arguments(NestedMockArguments)
    assert len(arguments) == 2, "There should be two click arguments for the nested dataclass."
    assert (
        arguments[0].name == "nested_arg__arg1"
    ), "The nested first argument name should be 'nested_arg__arg1'."
    assert (
        arguments[1].name == "nested_arg__arg2"
    ), "The nested second argument name should be 'nested_arg__arg2'."


def test_composition() -> None:
    CommandTree("base", "The base command")

    CommandTree("base", "The base command", (CommandTree("child", "The child command"),))


def test_get_attribute_docstring():
    @dataclass
    class MockDataclass:
        """MockDataclass description."""

        field: int
        """The field's docstring."""

    docstring = get_attribute_docstring(MockDataclass, "field")
    assert docstring == "The field's docstring.", "The docstring did not match the expected value"


def test_get_attribute_docstring_no_docstring():
    @dataclass
    class MockDataclass:
        field: int

    docstring = get_attribute_docstring(MockDataclass, "field")
    assert docstring == "", "The docstring should be empty for a field without a docstring"


def test_get_attribute_docstring_nonexistent_field():
    @dataclass
    class MockDataclass:
        field: int

    with pytest.raises(ValueError) as exc_info:
        get_attribute_docstring(MockDataclass, "nonexistent_field")
    assert (
        "Attribute nonexistent_field not found in dataclass rats_test.devtools.test_command_treetest_get_attribute_docstring_nonexistent_field.<locals>.MockDataclass"
        in str(exc_info.value)
    ), "The error message did not match the expected value"
