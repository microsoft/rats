from collections.abc import Iterator
from typing import NamedTuple

import click

from rats import apps as apps
from rats import cli as cli
from rats import logs as logs
from rats import projects


class CiCommandGroups(NamedTuple):
    """Main configuration object for the `rats-ci` subcommands."""

    install: tuple[tuple[str, ...], ...]
    """Set of commands meant to be run as part of `rats-ci install`."""

    fix: tuple[tuple[str, ...], ...]
    """Set of commands meant to be run as part of `rats-ci fix`."""

    check: tuple[tuple[str, ...], ...]
    """Set of commands meant to be run as part of `rats-ci check`."""

    test: tuple[tuple[str, ...], ...]
    """Set of commands meant to be run as part of `rats-ci test`."""


@apps.autoscope
class AppConfigs:
    COMMAND_GROUPS = apps.ServiceId[CiCommandGroups]("command-groups")
    """
    Brings together the individual commands into a single config object.

    Defining this service allows the entire configuration to be done in a single provider method,
    in case none of the defaults are desired.

    ```python
    from rats import apps, ci


    class PluginContainer(apps.Container, apps.PluginMixin):

        @apps.service(ci.AppConfigs.COMMAND_GROUPS)
        def _cmd_groups(self) -> CiCommandGroups:
            return CiCommandGroups(
                install=tuple(
                    tuple(["uv", "sync"]),
                ),
                fix=tuple(
                    tuple(["ruff", "check", "--fix"]),
                ),
                check=tuple(
                    tuple(["ruff", "check"]),
                ),
                test=tuple(
                    tuple(["pytest"]),
                ),
            )
    ```
    """
    INSTALL = apps.ServiceId[tuple[str, ...]]("install")
    """
    Service group to define commands run with `rats-ci install`.

    ```python
    from rats import apps, ci


    class PluginContainer(apps.Container, apps.PluginMixin):

        @apps.group(ci.AppConfigs.INSTALL)
        def _install_cmds(self) -> Iterator[tuple[str, ...]]:
            yield tuple(["uv", "sync"])
    ```
    """
    FIX = apps.ServiceId[tuple[str, ...]]("fix")
    """
    Service group to define commands run with `rats-ci fix`.

    ```python
    from rats import apps, ci


    class PluginContainer(apps.Container, apps.PluginMixin):

        @apps.group(ci.AppConfigs.FIX)
        def _fix_cmds(self) -> Iterator[tuple[str, ...]]:
            yield tuple(["ruff", "check", "--fix"])
    ```
    """
    CHECK = apps.ServiceId[tuple[str, ...]]("check")
    """
    Service group to define commands run with `rats-ci check`.

    ```python
    from rats import apps, ci


    class PluginContainer(apps.Container, apps.PluginMixin):

        @apps.group(ci.AppConfigs.CHECK)
        def _check_cmds(self) -> Iterator[tuple[str, ...]]:
            yield tuple(["ruff", "check")
    ```
    """
    TEST = apps.ServiceId[tuple[str, ...]]("test")
    """
    Service group to define commands run with `rats-ci test`.

    ```python
    from rats import apps, ci


    class PluginContainer(apps.Container, apps.PluginMixin):

        @apps.group(ci.AppConfigs.TEST)
        def _test_cmds(self) -> Iterator[tuple[str, ...]]:
            yield tuple(["pytest")
    ```
    """


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    """
    Main application for the `rats-ci` cli commands.

    Not typically used directly, but can be invoked using [rats.apps.AppBundle][] within tests or
    in advanced workflows.

    ```python
    from rats import apps, ci


    ci_app = apps.AppBundle(app_plugin=ci.Application)
    ci_app.install()
    ci_app.fix()
    ci_app.check()
    ci_app.test()
    ```

    !!! warning
        Calling `ci_app.execute()` is unlikely to behave as expected, because [sys.argv][] is
        parsed by the [click][] library.
    """

    def execute(self) -> None:
        """Parses [sys.argv][] to run the `rats-ci` cli application."""
        cli.create_group(
            click.Group(
                "rats-ci",
                help="commands used during ci/cd",
                chain=True,  # allow us to run more than one ci subcommand at once
            ),
            self,
        ).main()

    @cli.command()
    def config(self) -> None:
        """
        Show information about the configured command groups for active component.

        Refer to [rats.ci][] for details on how to update these values.
        """
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        command_groups = self._app.get(AppConfigs.COMMAND_GROUPS)

        print(f"component: {selected_component.component_name()}")
        for group, cmds in command_groups._asdict().items():
            print(f"  {group}")
            for cmd in cmds:
                print(f"    {' '.join(cmd)}")

    @cli.command()
    def install(self) -> None:
        """
        Install the development environment for the component.

        Refer to [rats.ci.AppConfigs.INSTALL][] for  details on how to update these values.
        """
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        command_groups = self._app.get(AppConfigs.COMMAND_GROUPS)

        for cmd in command_groups.install:
            selected_component.run(*cmd)

        print(f"ran {len(command_groups.install)} installation commands")

    @cli.command()
    def fix(self) -> None:
        """
        Run any configured auto-formatters for the component.

        Refer to [rats.ci.AppConfigs.FIX][] for  details on how to update these values.
        """
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        command_groups = self._app.get(AppConfigs.COMMAND_GROUPS)
        for cmd in command_groups.fix:
            selected_component.run(*cmd)

        print(f"ran {len(command_groups.fix)} fix commands")

    @cli.command()
    def check(self) -> None:
        """
        Run any configured linting & typing checks for the component.

        Refer to [rats.ci.AppConfigs.CHECK][] for  details on how to update these values.
        """
        selected_component = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        command_groups = self._app.get(AppConfigs.COMMAND_GROUPS)

        for cmd in command_groups.check:
            selected_component.run(*cmd)

        print(f"ran {len(command_groups.check)} check commands")

    @cli.command()
    def test(self) -> None:
        """
        Run any configured tests for the component.

        Refer to [rats.ci.AppConfigs.TEST][] for  details on how to update these values.
        """
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
        return apps.CompositeContainer(
            projects.PluginContainer(self._app),
            apps.PythonEntryPointContainer(self._app, "rats.ci"),
        )


def main() -> None:
    """The main entry-point for the application, used to define the python script for `rats-ci."""
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
