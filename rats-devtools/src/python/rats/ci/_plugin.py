from collections.abc import Iterator

import click

from rats import apps as apps
from rats import cli as cli
from rats import devtools, projects

from ._commands import CiCommandGroups, PluginCommands


@apps.autoscope
class PluginConfigs:
    COMMAND_GROUPS = apps.ServiceId[CiCommandGroups]("command-groups")
    INSTALL = apps.ServiceId[tuple[str, ...]]("install")
    FIX = apps.ServiceId[tuple[str, ...]]("fix")
    CHECK = apps.ServiceId[tuple[str, ...]]("check")
    TEST = apps.ServiceId[tuple[str, ...]]("test")


@apps.autoscope
class PluginServices:
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    MAIN_EXE = apps.ServiceId[apps.Executable]("main-exe")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")

    CONFIGS = PluginConfigs


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.PluginServices.EVENTS.OPENING)
    def _on_open(self) -> Iterator[apps.Executable]:
        def run() -> None:
            parent = self._app.get(devtools.PluginServices.MAIN_CLICK)
            ci = self._app.get(PluginServices.MAIN_CLICK)
            parent.add_command(ci)

        yield apps.App(run)

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=lambda: self._app.get(projects.PluginServices.PROJECT_TOOLS),
            selected_component=lambda: self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS),
            devtools_component=lambda: self._app.get(
                projects.PluginServices.DEVTOOLS_COMPONENT_TOOLS
            ),
            command_groups=lambda: self._app.get(PluginServices.CONFIGS.COMMAND_GROUPS),
        )

    @apps.fallback_service(PluginServices.CONFIGS.COMMAND_GROUPS)
    def _default_commands_config(self) -> CiCommandGroups:
        return CiCommandGroups(
            install=tuple(self._app.get_group(PluginConfigs.INSTALL)),
            fix=tuple(self._app.get_group(PluginConfigs.FIX)),
            check=tuple(self._app.get_group(PluginConfigs.CHECK)),
            test=tuple(self._app.get_group(PluginConfigs.TEST)),
        )

    @apps.fallback_group(PluginServices.CONFIGS.INSTALL)
    def _poetry_install(self) -> Iterator[tuple[str, ...]]:
        yield "poetry", "install"

    @apps.fallback_group(PluginServices.CONFIGS.FIX)
    def _ruff_format(self) -> Iterator[tuple[str, ...]]:
        yield "ruff", "format"

    @apps.fallback_group(PluginServices.CONFIGS.FIX)
    def _ruff_fix(self) -> Iterator[tuple[str, ...]]:
        yield "ruff", "check", "--fix", "--unsafe-fixes"

    @apps.fallback_group(PluginServices.CONFIGS.CHECK)
    def _ruff_format_check(self) -> Iterator[tuple[str, ...]]:
        yield "ruff", "format", "--check"

    @apps.fallback_group(PluginServices.CONFIGS.CHECK)
    def _ruff_check(self) -> Iterator[tuple[str, ...]]:
        yield "ruff", "check"

    @apps.fallback_group(PluginServices.CONFIGS.CHECK)
    def _pyright(self) -> Iterator[tuple[str, ...]]:
        yield ("pyright",)

    @apps.fallback_group(PluginServices.CONFIGS.TEST)
    def _pytest(self) -> Iterator[tuple[str, ...]]:
        yield ("pytest",)

    @apps.service(PluginServices.MAIN_EXE)
    def _main_exe(self) -> apps.Executable:
        return apps.App(lambda: self._app.get(PluginServices.MAIN_CLICK)())

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        command_container = self._app.get(PluginServices.COMMANDS)
        ci = click.Group(
            "ci",
            help="commands used during ci/cd",
            chain=True,  # allow us to run more than one ci subcommand at once
        )
        command_container.attach(ci)
        return ci
