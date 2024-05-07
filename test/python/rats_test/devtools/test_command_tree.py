import pytest
from dataclasses import dataclass
from rats.devtools._command_tree import get_attribute_docstring


@dataclass
class ExampleDataclass:
    """Example dataclass for testing."""

    attribute: int
    """This is the attribute's docstring."""


def test_get_attribute_docstring():
    docstring = get_attribute_docstring(ExampleDataclass, 'attribute')
    expected_docstring = "This is the attribute's docstring."
    assert docstring == expected_docstring, "The docstring should match the attribute's docstring."

def test_get_attribute_docstring_nonexistent_attribute():
    with pytest.raises(ValueError):
        get_attribute_docstring(ExampleDataclass, 'nonexistent_attribute')

def test_get_attribute_docstring_non_dataclass():
    with pytest.raises(AssertionError):
        get_attribute_docstring(object, 'attribute')
