from rats import apps
from rats import command_tree as command_tree

from ._ids import AppServices


class DevtoolsCliTreePlugin(apps.AnnotatedContainer):
    def __init__(self, app: apps.Container) -> None:
        self._app = app

    # @apps.service(AppServices.CLI_EXE)
    def command_tree_cli_exe(self) -> apps.Executable:
        return command_tree.CommandTreeClickExecutable(self._app.get(AppServices.CLI_COMMAND_TREE))

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
                for child in self._app.get_group(
                    command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools")
                )
            ),
        )
