from rats import apps

from ._command_service_tree import CommandServiceTree
from ._command_tree import CommandTree


@apps.autoscope
class CommandTreeGroups:
    @staticmethod
    def subcommands(name: str) -> apps.ServiceId[CommandTree | CommandServiceTree]:
        return apps.ServiceId(f"command-tree-subcommands[{name}]")


@apps.autoscope
class CommandTreeServices:
    @staticmethod
    def command(name: str) -> apps.ServiceId[CommandTree | CommandServiceTree]:
        return apps.ServiceId(f"command-tree[{name}]")

    GROUPS = CommandTreeGroups
