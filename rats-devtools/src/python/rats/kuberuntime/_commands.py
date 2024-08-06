# type: ignore[reportUntypedFunctionDecorator]
import json
import logging
import os
from pathlib import Path

import click

from rats import apps, cli, projects

logger = logging.getLogger(__name__)


class PluginCommands(cli.CommandContainer):
    _project_tools: projects.ProjectTools
    _worker_node_runtime: apps.Runtime
    _k8s_runtime: apps.Runtime

    def __init__(
        self,
        project_tools: projects.ProjectTools,
        worker_node_runtime: apps.Runtime,
        k8s_runtime: apps.Runtime,
    ) -> None:
        self._project_tools = project_tools
        self._worker_node_runtime = worker_node_runtime
        self._k8s_runtime = k8s_runtime

    @cli.command()
    @click.option("--exe-id", multiple=True)
    @click.option("--group-id", multiple=True)
    def submit(self, exe_id: tuple[str, ...], group_id: tuple[str, ...]) -> None:
        if len(exe_id) == 0 and len(group_id) == 0:
            raise ValueError("No executables or groups were passed to the command")

        self._project_tools.build_component_image(Path().resolve().name)

        exes = [apps.ServiceId[apps.Executable](exe) for exe in exe_id]
        groups = [apps.ServiceId[apps.Executable](group) for group in group_id]
        # we can join these into one job later if needed
        if len(exes):
            self._k8s_runtime.execute(*exes)

        if len(groups):
            self._k8s_runtime.execute_group(*groups)

    @cli.command()
    def worker_node(self) -> None:
        """
        Run the worker node process.

        This command is intended to be run in a k8s job. It will execute any exes and groups
        that are passed to it through environment variables.
        """
        exe_ids = json.loads(
            os.environ.get("DEVTOOLS_K8S_EXE_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )
        group_ids = json.loads(
            os.environ.get("DEVTOOLS_K8S_EVENT_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )

        self._worker_node_runtime.execute(*exe_ids)
        self._worker_node_runtime.execute_group(*group_ids)
