from dataclasses import dataclass
from typing import Any

import click
import pytest

from rats.devtools._command_tree import CommandTree, get_attribute_docstring


class ProgrammaticExecutionGroup(click.Group):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Alias for :meth:`main`."""
        return self.main(*args, standalone_mode=False, **kwargs)


from rats.devtools._command_tree import CommandTree, get_attribute_docstring, dataclass_to_click_arguments

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
    assert arguments[0].name == "--arg1", "The first argument name should be '--arg1'."
    assert arguments[1].name == "--arg2", "The second argument name should be '--arg2'."

def test_dataclass_to_click_arguments_nested():
    arguments = dataclass_to_click_arguments(NestedMockArguments)
    assert len(arguments) == 2, "There should be two click arguments for the nested dataclass."
    assert arguments[0].name == "--nested_arg.arg1", "The nested first argument name should be '--nested_arg.arg1'."
    assert arguments[1].name == "--nested_arg.arg2", "The nested second argument name should be '--nested_arg.arg2'."

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
