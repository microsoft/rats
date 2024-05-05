from unittest import mock
from unittest.mock import MagicMock, create_autospec

import click

from rats.apps import PluginRunner
from rats.cli import AttachClickCommands, ClickExecutable


@mock.patch("click.Group")
def test_command_group_execute_registers_commands(m_click_group: MagicMock):
    registered_plugins = []

    class MockPlugin:
        def on_group_open(self, group: click.Group) -> None:
            registered_plugins.append(self)

    plugin1 = MockPlugin()
    plugin2 = MockPlugin()

    m_group_instance = m_click_group.return_value

    command_group = ClickExecutable(
        command=lambda: m_group_instance,
        plugins=PluginRunner(iter([plugin1, plugin2])),
    )
    command_group.execute()

    assert len(registered_plugins) == 2
    assert plugin1 in registered_plugins
    assert plugin2 in registered_plugins
    m_group_instance.assert_called_once()


def test_group_commands_on_group_registration():
    mock_command = create_autospec(spec=click.Command, instance=True)
    group_commands = AttachClickCommands(commands=iter([mock_command]))
    mock_group = create_autospec(spec=click.Group, instance=True)
    group_commands.on_group_open(mock_group)
    mock_group.add_command.assert_called_once_with(mock_command)
