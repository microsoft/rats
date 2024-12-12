# type: ignore[reportUntypedFunctionDecorator]
import logging
from typing import NamedTuple

from rats import apps, cli, projects

logger = logging.getLogger(__name__)


class CiCommandGroups(NamedTuple):
    install: tuple[tuple[str, ...], ...]
    fix: tuple[tuple[str, ...], ...]
    check: tuple[tuple[str, ...], ...]
    test: tuple[tuple[str, ...], ...]


class PluginCommands(cli.Container):
    _project_tools: apps.Provider[projects.ProjectTools]
    _selected_component: apps.Provider[projects.ComponentTools]
    _devtools_component: apps.Provider[projects.ComponentTools]
    _command_groups: apps.Provider[CiCommandGroups]

    def __init__(
        self,
        project_tools: apps.Provider[projects.ProjectTools],
        selected_component: apps.Provider[projects.ComponentTools],
        devtools_component: apps.Provider[projects.ComponentTools],
        command_groups: apps.Provider[CiCommandGroups],
    ) -> None:
        self._project_tools = project_tools
        self._selected_component = selected_component
        self._devtools_component = devtools_component
        self._command_groups = command_groups

    @cli.command()
    def install(self) -> None:
        """Install the development environment for the component."""
        for cmd in self._command_groups().install:
            self._selected_component().run(*cmd)
        print(f"ran {len(self._command_groups().install)} installation commands")

    @cli.command()
    def fix(self) -> None:
        """Run any configured auto-formatters for the component."""
        for cmd in self._command_groups().fix:
            self._selected_component().run(*cmd)
        print(f"ran {len(self._command_groups().fix)} fix commands")

    @cli.command()
    def check(self) -> None:
        """Run any configured linting & typing checks for the component."""
        for cmd in self._command_groups().check:
            self._selected_component().run(*cmd)
        print(f"ran {len(self._command_groups().check)} check commands")

    @cli.command()
    def test(self) -> None:
        """Run any configured tests for the component."""
        for cmd in self._command_groups().test:
            self._selected_component().run(*cmd)
        print(f"ran {len(self._command_groups().test)} test commands")

    @cli.command()
    def build_image(self) -> None:
        """Build a container image of the component."""
        self._project_tools().build_component_image(self._selected_component().find_path(".").name)
