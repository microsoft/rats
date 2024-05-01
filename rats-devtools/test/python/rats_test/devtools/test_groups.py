from unittest import mock
from unittest.mock import MagicMock, create_autospec

import click
import pytest

from rats.devtools._groups import (
    CommandGroup,
    CommandProvider,
    GroupCommands,
    LazyClickGroup,
    PluginRunner,
)


@mock.patch("click.Group")
def test_command_group_execute_registers_commands(m_click_group: MagicMock):
    registered_plugins = []

    class MockPlugin:
        def on_group_registration(self, group: click.Group) -> None:
            registered_plugins.append(self)

    plugin1 = MockPlugin()
    plugin2 = MockPlugin()

    m_group_instance = m_click_group.return_value

    command_group = CommandGroup(plugins=PluginRunner(iter([plugin1, plugin2])))
    command_group.execute()

    assert len(registered_plugins) == 2
    assert plugin1 in registered_plugins
    assert plugin2 in registered_plugins
    m_click_group.assert_called_once()
    m_group_instance.assert_called_once()


def test_command_provider_get_command():
    mock_command = create_autospec(spec=click.Command, instance=True)
    command_provider = CommandProvider(commands={"test": lambda: mock_command})
    assert command_provider.get("test") == mock_command


def test_command_provider_get_command_not_found():
    command_provider = CommandProvider(commands={})
    with pytest.raises(ValueError):
        command_provider.get("nonexistent")


def test_lazy_click_group_get_command():
    mock_command = create_autospec(spec=click.Command, instance=True)
    command_provider = CommandProvider(commands={"test": lambda: mock_command})
    lazy_group = LazyClickGroup(name="test_group", provider=command_provider)
    assert lazy_group.get_command(click.Context(lazy_group), "test") == mock_command


def test_lazy_click_group_list_commands():
    command_provider = CommandProvider(commands={"test": lambda: click.Command(name="test")})
    lazy_group = LazyClickGroup(name="test_group", provider=command_provider)
    assert lazy_group.list_commands(click.Context(lazy_group)) == ["test"]


def test_group_commands_on_group_registration():
    mock_command = create_autospec(spec=click.Command, instance=True)
    group_commands = GroupCommands(commands=iter([mock_command]))
    mock_group = create_autospec(spec=click.Group, instance=True)
    group_commands.on_group_registration(mock_group)
    mock_group.add_command.assert_called_once_with(mock_command)
