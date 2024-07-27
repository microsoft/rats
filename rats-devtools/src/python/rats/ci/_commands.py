# type: ignore[reportUntypedFunctionDecorator]
import json
import logging
import os
import uuid
from collections.abc import Iterable
from pathlib import Path

import click

from rats import apps, cli, projects

logger = logging.getLogger(__name__)


class PluginCommands(cli.CommandContainer):
    _project_tools: projects.ProjectTools
    _selected_component: projects.ComponentOperations
    _devtools_component: projects.ComponentOperations
    _worker_node_runtime: apps.Runtime
    _k8s_runtime: apps.Runtime
    _devtools_runtime: apps.Runtime
    _minimal_runtime: apps.Runtime

    def __init__(
        self,
        project_tools: projects.ProjectTools,
        selected_component: projects.ComponentOperations,
        devtools_component: projects.ComponentOperations,
        worker_node_runtime: apps.Runtime,
        k8s_runtime: apps.Runtime,
        devtools_runtime: apps.Runtime,
        minimal_runtime: apps.Runtime,
    ) -> None:
        self._project_tools = project_tools
        self._selected_component = selected_component
        self._devtools_component = devtools_component
        self._worker_node_runtime = worker_node_runtime
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
    @click.option("--exe-id", multiple=True)
    @click.option("--group-id", multiple=True)
    def example_k8s_runtime(self, exe_id: tuple[str, ...], group_id: tuple[str, ...]) -> None:
        if len(exe_id) == 0 and len(group_id) == 0:
            raise ValueError("No executables or groups were passed to the command")

        # just forcefully build all our images
        self._project_tools.build_component_images()

        exes = [apps.ServiceId[apps.Executable](exe) for exe in exe_id]
        groups = [apps.ServiceId[apps.Executable](group) for group in group_id]
        if len(exes):
            self._k8s_runtime.execute(*exes)
            self._minimal_runtime.execute(*exes)

        if len(groups):
            self._k8s_runtime.execute_group(*groups)

    @cli.command(cli.CommandId.auto())
    def ping(self) -> None:
        for _x in range(20):
            print(json.dumps({"pong": str(uuid.uuid4())}))

    @cli.command(cli.CommandId.auto())
    def worker_node(self) -> None:
        """
        Run the worker node process.

        This command is intended to be run in a kubernetes job. It will execute any exes and groups
        that are passed to it by the kubernetes job. Currently, the exes and groups are passed as
        environment variables until a proper mechanism is implemented.
        """
        exe_ids = json.loads(
            os.environ.get("DEVTOOLS_K8S_EXE_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )
        group_ids = json.loads(
            os.environ.get("DEVTOOLS_K8S_GROUP_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )

        annotation_exe_ids = Path("/etc/podinfo/annotations/rats.kuberuntime/exe-ids")
        annotation_group_ids = Path("/etc/podinfo/annotations/rats.kuberuntime/group-ids")

        if annotation_exe_ids.exists():
            try:
                exe_ids += json.loads(
                    annotation_exe_ids.read_text(),
                    object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
                )
            except json.JSONDecodeError:
                pass

        if annotation_group_ids.exists():
            try:
                group_ids += json.loads(
                    annotation_group_ids.read_text(),
                    object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
                )
            except json.JSONDecodeError:
                pass

        self._worker_node_runtime.execute(*exe_ids)
        self._worker_node_runtime.execute_group(*group_ids)
