import click

from rats import apps as apps
from rats import cli as cli
from rats import command_tree as command_tree


@apps.autoscope
class AppGroups:
    CLI_ROOT_PLUGINS = apps.ServiceId[cli.ClickGroupPlugin]("cli-plugins[root]")
    CLI_ROOT_COMMANDS = apps.ServiceId[click.Command]("cli-commands[root]")

    @staticmethod
    def commands(group: click.Group) -> apps.ServiceId[cli.ClickGroupPlugin]:
        return apps.ServiceId[cli.ClickGroupPlugin](f"cli-plugins[{group.name}]")


@apps.autoscope
class AppServices:
    CLI_EXE = apps.ServiceId[apps.Executable]("cli-exe")
    CLI_COMMAND_TREE = apps.ServiceId[command_tree.CommandTree]("cli-command-tree")
    GROUPS = AppGroups
