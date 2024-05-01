from dataclasses import dataclass
from typing import Any

import click
import pytest

from rats.devtools._command_tree import CommandTree, get_attribute_docstring


class ProgrammaticExecutionGroup(click.Group):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Alias for :meth:`main`."""
        return self.main(*args, standalone_mode=False, **kwargs)


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
