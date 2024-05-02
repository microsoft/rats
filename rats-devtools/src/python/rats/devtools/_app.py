import logging

import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli as cli

from ._groups import CommandGroup, GroupCommands
from ._plugins import PluginRunner


@apps.autoscope
class AppGroups:
    CLI_ROOT_PLUGINS = apps.ServiceId[cli.CommandGroupPlugin]("cli-plugins[root]")
    CLI_ROOT_COMMANDS = apps.ServiceId[click.Command]("cli-commands[root]")


@apps.autoscope
class AppServices:
    CLI_EXE = apps.ServiceId[apps.Executable]("cli-exe")
    GROUPS = AppGroups


class AppContainer(apps.AnnotatedContainer):
    @apps.service(AppServices.CLI_EXE)
    def cli_exe(self) -> CommandGroup:
        return CommandGroup(PluginRunner(self.get_group(AppServices.GROUPS.CLI_ROOT_PLUGINS)))

    @apps.group(AppServices.GROUPS.CLI_ROOT_PLUGINS)
    def root_commands_plugin(self) -> GroupCommands:
        return GroupCommands(self.get_group(AppServices.GROUPS.CLI_ROOT_COMMANDS))

    @apps.container()
    def plugins(self) -> apps.Container:
        return apps.PluginContainers(self, "rats.devtools.plugins")


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    container = AppContainer()
    container.get(AppServices.CLI_EXE).execute()
