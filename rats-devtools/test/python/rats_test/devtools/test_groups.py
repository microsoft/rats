from unittest.mock import create_autospec

import click

from rats.cli import AttachClickCommands


def test_group_commands_on_group_registration():
    mock_command = create_autospec(spec=click.Command, instance=True)
    group_commands = AttachClickCommands(commands=iter([mock_command]))
    mock_group = create_autospec(spec=click.Group, instance=True)
    group_commands.on_group_open(mock_group)
    mock_group.add_command.assert_called_once_with(mock_command)
