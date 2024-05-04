from unittest.mock import create_autospec

import click
import pytest

from rats.cli import ClickCommandMapper


def test_command_provider_get_command():
    mock_command = create_autospec(spec=click.Command, instance=True)
    command_provider = ClickCommandMapper(commands={"test": lambda: mock_command})
    assert command_provider.get("test") == mock_command


def test_command_provider_get_command_not_found():
    command_provider = ClickCommandMapper(commands={})
    with pytest.raises(ValueError):
        command_provider.get("nonexistent")


# def test_lazy_click_group_get_command():
#     mock_command = create_autospec(spec=click.Command, instance=True)
#     command_provider = ClickCommandMapper(commands={"test": lambda: mock_command})
#     lazy_group = ClickCommandGroup(name="test_group", provider=command_provider)
#     assert lazy_group.get_command(click.Context(lazy_group), "test") == mock_command
#
#
# def test_lazy_click_group_list_commands():
#     command_provider = ClickCommandMapper(commands={"test": lambda: click.Command(name="test")})
#     lazy_group = ClickCommandGroup(name="test_group", provider=command_provider)
#     assert lazy_group.list_commands(click.Context(lazy_group)) == ["test"]
