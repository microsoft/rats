# type: ignore[reportUntypedFunctionDecorator]
import logging

from rats import apps, cli, projects

logger = logging.getLogger(__name__)


class PluginCommands(cli.Container):
    """These are the base commands you get with devtools."""

    _project_tools: apps.Provider[projects.ProjectTools]

    def __init__(
        self,
        project_tools: apps.Provider[projects.ProjectTools],
    ) -> None:
        self._project_tools = project_tools

    @cli.command()
    def project_info(self) -> None:
        """Show everything we know about this project."""
        print(f"repo root: {self._project_tools().repo_root().resolve()}")
        print("detected components:")
        for component in self._project_tools().discover_components():
            if component == self._project_tools().devtools_component():
                print(f"🛠 {component.name}")
            else:
                print(f"   {component.name}")

    @cli.command()
    def project_hash(self) -> None:
        """Calculate the hash of the project manifest."""
        print(self._project_tools().image_context_hash())

    @cli.command()
    def project_manifest(self) -> None:
        """Show the project manifest."""
        print(self._project_tools().image_context_manifest())
