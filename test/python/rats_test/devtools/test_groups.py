import pytest
from unittest.mock import Mock, create_autospec
import click
from rats.devtools._groups import CommandGroup, CommandProvider, LazyClickGroup, GroupCommands, CommandGroupPlugin


def test_command_group_execute_registers_commands():
    mock_plugin_runner = create_autospec(spec=CommandGroupPlugin, instance=True)
    command_group = CommandGroup(plugins=mock_plugin_runner)
    command_group.execute()
    mock_plugin_runner.apply.assert_called_once()


def test_command_provider_get_command():
    mock_command = create_autospec(spec=click.Command, instance=True)
    command_provider = CommandProvider(commands={'test': lambda: mock_command})
    assert command_provider.get('test') == mock_command


def test_command_provider_get_command_not_found():
    command_provider = CommandProvider(commands={})
    with pytest.raises(ValueError):
        command_provider.get('nonexistent')


def test_lazy_click_group_get_command():
    mock_command = create_autospec(spec=click.Command, instance=True)
    command_provider = CommandProvider(commands={'test': lambda: mock_command})
    lazy_group = LazyClickGroup(name='test_group', provider=command_provider)
    assert lazy_group.get_command(click.Context(lazy_group), 'test') == mock_command


def test_lazy_click_group_list_commands():
    command_provider = CommandProvider(commands={'test': lambda: click.Command(name='test')})
    lazy_group = LazyClickGroup(name='test_group', provider=command_provider)
    assert lazy_group.list_commands(click.Context(lazy_group)) == ['test']


def test_group_commands_on_group_registration():
    mock_command = create_autospec(spec=click.Command, instance=True)
    group_commands = GroupCommands(commands=iter([mock_command]))
    mock_group = create_autospec(spec=click.Group, instance=True)
    group_commands.on_group_registration(mock_group)
    mock_group.add_command.assert_called_once_with(mock_command)
