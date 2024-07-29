# type: ignore[reportUntypedFunctionDecorator]
import json
import logging
import uuid
from collections.abc import Iterable

import click

from rats import apps, cli, projects

logger = logging.getLogger(__name__)


class PluginCommands(cli.CommandContainer):
    _project_tools: projects.ProjectTools
    _selected_component: projects.ComponentOperations
    _devtools_component: projects.ComponentOperations
    _ping: apps.Executable
    _pong: apps.Executable
    _standard_runtime: apps.Runtime
    _k8s_runtime: apps.Runtime
    _devtools_runtime: apps.Runtime
    _minimal_runtime: apps.Runtime

    def __init__(
        self,
        project_tools: projects.ProjectTools,
        selected_component: projects.ComponentOperations,
        devtools_component: projects.ComponentOperations,
        ping: apps.Executable,
        pong: apps.Executable,
        standard_runtime: apps.Runtime,
        k8s_runtime: apps.Runtime,
        devtools_runtime: apps.Runtime,
        minimal_runtime: apps.Runtime,
    ) -> None:
        self._project_tools = project_tools
        self._selected_component = selected_component
        self._devtools_component = devtools_component
        self._ping = ping
        self._pong = pong
        self._standard_runtime = standard_runtime
        self._k8s_runtime = k8s_runtime
        self._devtools_runtime = devtools_runtime
        self._minimal_runtime = minimal_runtime

    @cli.command(cli.CommandId.auto())
    def install(self) -> None:
        """
        Install the package in the current environment.

        Typically, this just require running `poetry install`. However, some components may run
        additional steps to make the package ready for development. This command does not
        necessarily represent the steps required to install the package in a production
        environments.
        """
        self._selected_component.install()

    @cli.command(cli.CommandId.auto())
    def all_checks(self) -> None:
        """
        Run all the required checks for the component.

        In many cases, if this command completes without error, the CI pipelines in the Pull
        Request should also pass. If the checks for a component run quickly enough, this command
        can be used as a pre-commit hook.
        """
        self._selected_component.pytest()
        self._selected_component.pyright()
        self._selected_component.ruff("format", "--check")
        self._selected_component.ruff("check")

    @cli.command(cli.CommandId.auto())
    @click.argument("files", nargs=-1, type=click.Path(exists=True))
    def fix(self, files: Iterable[str]) -> None:
        """Run any configured auto-formatters for the component."""
        self._selected_component.run("ruff", "format", *files)
        self._selected_component.run("ruff", "check", "--fix", "--unsafe-fixes", *files)

    @cli.command(cli.CommandId.auto())  # type: ignore[reportArgumentType]
    @click.argument("version")
    def update_version(self, version: str) -> None:
        """Update the version of the package found in pyproject.toml."""
        self._selected_component.poetry("version", version)

    @cli.command(cli.CommandId.auto())
    def build_wheel(self) -> None:
        """Build a wheel for the package."""
        self._selected_component.poetry("build", "-f", "wheel")

    @cli.command(cli.CommandId.auto())  # type: ignore[reportArgumentType]
    def build_image(self) -> None:
        """Update the version of the package found in pyproject.toml."""
        self._project_tools.build_component_image(self._selected_component.find_path(".").name)

    @cli.command(cli.CommandId.auto())  # type: ignore[reportArgumentType]
    @click.argument("repository_name")
    def publish_wheel(self, repository_name: str) -> None:
        """
        Publish the wheel to the specified repository.

        This command assumes the caller has the required permissions and the specified repository
        has been configured with poetry.
        """
        self._selected_component.poetry(
            "publish",
            "--repository",
            repository_name,
            "--no-interaction",
            # temporarily skip existing during testing
            "--skip-existing",
        )

    @cli.command(cli.CommandId.auto())
    def ping(self) -> None:
        self._ping.execute()

    @cli.command(cli.CommandId.auto())
    def pong(self) -> None:
        self._pong.execute()
