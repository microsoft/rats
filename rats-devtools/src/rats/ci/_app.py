from collections.abc import Iterator
from typing import NamedTuple

import click

from rats import apps as apps
from rats import cli as cli
from rats import logs as logs
from rats import projects


class CiCommandGroups(NamedTuple):
    install: tuple[tuple[str, ...], ...]
    fix: tuple[tuple[str, ...], ...]
    check: tuple[tuple[str, ...], ...]
    test: tuple[tuple[str, ...], ...]


@apps.autoscope
class AppConfigs:
    COMMAND_GROUPS = apps.ServiceId[CiCommandGroups]("command-groups")
    INSTALL = apps.ServiceId[tuple[str, ...]]("install")
    FIX = apps.ServiceId[tuple[str, ...]]("fix")
    CHECK = apps.ServiceId[tuple[str, ...]]("check")
    TEST = apps.ServiceId[tuple[str, ...]]("test")


@apps.autoscope
class AppServices:
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        cli.create_group(
            click.Group(
                "rats-ci",
                help="commands used during ci/cd",
                chain=True,  # allow us to run more than one ci subcommand at once
            ),
            self,
        ).main()

    @cli.command()
    def install(self) -> None:
        """Install the development environment for the component."""
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        command_groups = self._app.get(AppConfigs.COMMAND_GROUPS)

        for cmd in command_groups.install:
            selected_component.run(*cmd)
            print(f"ran {len(command_groups.install)} installation commands")

    @cli.command()
    def fix(self) -> None:
        """Run any configured auto-formatters for the component."""
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        command_groups = self._app.get(AppConfigs.COMMAND_GROUPS)

        for cmd in command_groups.fix:
            selected_component.run(*cmd)
            print(f"ran {len(command_groups.fix)} fix commands")

    @cli.command()
    def check(self) -> None:
        """Run any configured linting & typing checks for the component."""
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        command_groups = self._app.get(AppConfigs.COMMAND_GROUPS)

        for cmd in command_groups.check:
            selected_component.run(*cmd)
            print(f"ran {len(command_groups.check)} check commands")

    @cli.command()
    def test(self) -> None:
        """Run any configured tests for the component."""
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        command_groups = self._app.get(AppConfigs.COMMAND_GROUPS)

        for cmd in command_groups.test:
            selected_component.run(*cmd)
            print(f"ran {len(command_groups.test)} test commands")

    @cli.command()
    def build_image(self) -> None:
        """Build a container image of the component."""
        project_tools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)

        project_tools.build_component_image(selected_component.find_path(".").name)

    @apps.fallback_service(AppConfigs.COMMAND_GROUPS)
    def _default_commands_config(self) -> CiCommandGroups:
        return CiCommandGroups(
            install=tuple(self._app.get_group(AppConfigs.INSTALL)),
            fix=tuple(self._app.get_group(AppConfigs.FIX)),
            check=tuple(self._app.get_group(AppConfigs.CHECK)),
            test=tuple(self._app.get_group(AppConfigs.TEST)),
        )

    @apps.fallback_group(AppConfigs.INSTALL)
    def _poetry_install(self) -> Iterator[tuple[str, ...]]:
        yield "poetry", "install"

    @apps.fallback_group(AppConfigs.FIX)
    def _ruff_format(self) -> Iterator[tuple[str, ...]]:
        yield "ruff", "format"

    @apps.fallback_group(AppConfigs.FIX)
    def _ruff_fix(self) -> Iterator[tuple[str, ...]]:
        yield "ruff", "check", "--fix", "--unsafe-fixes"

    @apps.fallback_group(AppConfigs.CHECK)
    def _default_checks(self) -> Iterator[tuple[str, ...]]:
        yield "ruff", "format", "--check"
        yield "ruff", "check"
        yield ("pyright",)

    @apps.fallback_group(AppConfigs.TEST)
    def _pytest(self) -> Iterator[tuple[str, ...]]:
        yield ("pytest",)

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(projects.PluginContainer(self._app))


def main() -> None:
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
