import logging

import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
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


class AppContainer(apps.AnnotatedContainer):
    # @apps.service(AppServices.CLI_EXE)
    def command_tree_cli_exe(self) -> apps.Executable:
        return command_tree.CommandTreeClickExecutable(self.get(AppServices.CLI_COMMAND_TREE))

    @apps.service(AppServices.CLI_COMMAND_TREE)
    def cli_command_tree(self) -> command_tree.CommandTree:
        return command_tree.CommandTree(
            name="rats-devtools",
            description="",
            children=tuple(
                (
                    child.to_command_tree(self)
                    if isinstance(child, command_tree.CommandServiceTree)
                    else child
                )
                for child in self.get_group(
                    command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools")
                )
            ),
        )

    @apps.service(AppServices.CLI_EXE)
    def cli_exe(self) -> apps.Executable:
        return cli.ClickExecutable(
            command=lambda: click.Group(),
            plugins=apps.PluginRunner(self.get_group(AppServices.GROUPS.CLI_ROOT_PLUGINS)),
        )

    @apps.group(AppServices.GROUPS.CLI_ROOT_PLUGINS)
    def root_commands_plugin(self) -> cli.GroupCommands:
        return cli.GroupCommands(self.get_group(AppServices.GROUPS.CLI_ROOT_COMMANDS))

    @apps.container()
    def plugins(self) -> apps.Container:
        return apps.PluginContainers(self, "rats.devtools.plugins")


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    container = AppContainer()
    container.get(AppServices.CLI_EXE).execute()
