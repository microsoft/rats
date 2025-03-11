from dataclasses import dataclass

import pytest

from rats.command_tree import (
    get_attribute_docstring,
)


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
        f"Attribute nonexistent_field not found in dataclass {__name__}.test_get_attribute_docstring_nonexistent_field.<locals>.MockDataclass"  # noqa: E501
        in str(exc_info.value)
    ), "The error message did not match the expected value"
