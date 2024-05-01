from dataclasses import dataclass
from unittest import mock

import click

from rats.command_tree import (
    CommandTree,
    dataclass_to_click_arguments,
    to_click_commands,
)


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


@dataclass
class MockTupleArguments:
    """MockTupleArguments description."""

    arg1: tuple[int, ...]
    """A tuple argument."""


def test_dataclass_to_click_arguments_tuple():
    arguments = dataclass_to_click_arguments(MockTupleArguments)
    assert len(arguments) == 1, "There should be one click argument for the tuple field."
    assert arguments[0].name == "arg1", "The tuple argument name should be 'arg1'."
    assert (
        arguments[0].type is click.INT
    ), "The tuple argument should be of type click.types.Tuple."
    assert arguments[0].multiple is True, "The tuple argument should have 'multiple' set to True."


@dataclass
class MockNestedTupleArguments:
    """MockNestedTupleArguments description."""

    arg1: tuple[MockArguments, ...]
    """A tuple of MockArguments."""


def test_dataclass_to_click_arguments_nested_tuple():
    arguments = dataclass_to_click_arguments(MockNestedTupleArguments)
    assert len(arguments) == 2, "There should be two click arguments for the nested tuple field."
    assert (
        arguments[0].name == "arg1__arg1"
    ), "The nested tuple first argument name should be 'arg1__arg1'."
    assert (
        arguments[1].name == "arg1__arg2"
    ), "The nested tuple second argument name should be 'arg1__arg2'."
    assert (
        arguments[0].type is click.STRING
    ), "The nested tuple first argument should be of type click.types.Tuple."
    assert (
        arguments[1].type is click.INT
    ), "The nested tuple second argument should be of type click.types.Tuple."
    assert (
        arguments[0].multiple is True
    ), "The nested tuple first argument should have 'multiple' set to True."
    assert (
        arguments[1].multiple is True
    ), "The nested tuple second argument should have 'multiple' set to True."


def test_to_click_commands_leaf_node():
    def test_handler():
        click.echo("Handler executed")

    command_tree = CommandTree(name="test", description="Test command", handler=test_handler)
    click_command = to_click_commands(command_tree)
    assert isinstance(
        click_command, click.Command
    ), "The result should be a click.Command instance"
    assert click_command.name == "test", "The command name should be 'test'"
    assert click_command.help == "Test command", "The command help should be 'Test command'"
    assert click_command.callback is not None, "The command should have a callback"
    assert (
        click_command.callback.__qualname__
        == "test_to_click_commands_leaf_node.<locals>.test_handler"
    ), "The callback should have the same name as the wrapped function"
    assert (
        click_command.callback.__wrapped__ == test_handler
    ), "The command callback should wrap the test_handler function"


def test_to_click_commands_with_children():
    def test_handler():
        click.echo("Handler executed")

    child_command_tree = CommandTree(
        name="child", description="Child command", handler=test_handler
    )
    parent_command_tree = CommandTree(
        name="parent", description="Parent command", children=(child_command_tree,)
    )
    click_group = to_click_commands(parent_command_tree)
    assert isinstance(click_group, click.Group), "The result should be a click.Group instance"
    assert click_group.name == "parent", "The group name should be 'parent'"
    assert click_group.help == "Parent command", "The group help should be 'Parent command'"
    assert "child" in click_group.commands, "The group should contain the 'child' command"

    with mock.patch("sys.argv", ["parent"]):
        click_group(standalone_mode=False)


def test_to_click_commands_with_arguments():
    @dataclass
    class TestArguments:
        arg1: str
        arg2: int

    def test_handler(test_arguments: TestArguments):
        assert isinstance(
            test_arguments, TestArguments
        ), "The argument should be a TestArguments instance"

    command_tree = CommandTree(
        name="test",
        description="Test command with arguments",
        kwargs_class=TestArguments,
        handler=test_handler,
    )
    click_command = to_click_commands(command_tree)
    assert isinstance(
        click_command, click.Command
    ), "The result should be a click.Command instance"
    assert click_command.name == "test", "The command name should be 'test'"
    assert (
        click_command.help == "Test command with arguments"
    ), "The command help should be 'Test command with arguments'"
    assert len(click_command.params) == 2, "The command should have two parameters"
    assert click_command.params[0].name == "arg1", "The first parameter should be 'arg1'"
    assert click_command.params[1].name == "arg2", "The second parameter should be 'arg2'"
    assert click_command.callback is not None, "The command should have a callback"
    assert (
        click_command.callback.__qualname__
        == "test_to_click_commands_with_arguments.<locals>.test_handler"
    ), "The callback should have the same name as the wrapped function"
    assert (
        click_command.callback.__wrapped__ == test_handler
    ), "The command callback should wrap the test_handler function"

    with mock.patch("sys.argv", ["test", "--arg1", "test-str", "--arg2", "2"]):
        click_command(standalone_mode=False)
