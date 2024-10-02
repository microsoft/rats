# type: ignore[reportUntypedFunctionDecorator]
import json
import logging
import os
from collections.abc import Iterator

import click

from rats import apps, cli, projects

logger = logging.getLogger(__name__)


class PluginCommands(cli.Container):
    _project_tools: apps.Provider[projects.ProjectTools]
    _cwd_component_tools: apps.Provider[projects.ComponentTools]
    _worker_node_runtime: apps.Provider[apps.Runtime]
    _aml_runtime: apps.Provider[apps.Runtime]
    _aml_exes: apps.Provider[Iterator[apps.ServiceId[apps.Executable], ...]]

    def __init__(
        self,
        project_tools: apps.Provider[projects.ProjectTools],
        cwd_component_tools: apps.Provider[projects.ComponentTools],
        standard_runtime: apps.Provider[apps.Runtime],
        aml_runtime: apps.Provider[apps.Runtime],
        aml_exes: apps.Provider[Iterator[apps.ServiceId[apps.Executable], ...]],
    ) -> None:
        self._project_tools = project_tools
        self._cwd_component_tools = cwd_component_tools
        self._worker_node_runtime = standard_runtime
        self._aml_runtime = aml_runtime
        self._aml_exes = aml_exes

    @cli.command()
    def _list(self) -> None:
        """List all the exes and groups that announce their availability to be submitted to aml."""
        for exe in self._aml_exes():
            click.echo(f"Exe: {exe.name}")

    @cli.command()
    @click.option("--exe-id", multiple=True)
    @click.option("--group-id", multiple=True)
    def submit(self, exe_id: tuple[str, ...], group_id: tuple[str, ...]) -> None:
        """Submit one or more exes and groups to aml."""
        if len(exe_id) == 0 and len(group_id) == 0:
            raise ValueError("No executables or groups were passed to the command")

        self._project_tools().build_component_image(self._cwd_component_tools().component_name())

        exes = [apps.ServiceId[apps.Executable](exe) for exe in exe_id]
        groups = [apps.ServiceId[apps.Executable](group) for group in group_id]
        # we can join these into one job later if needed
        if len(exes):
            self._aml_runtime().execute(*exes)

        if len(groups):
            self._aml_runtime().execute_group(*groups)

    @cli.command()
    def worker_node(self) -> None:
        """
        Run the worker node process.

        This command is intended to be run in an aml job. It will execute any exes and groups
        that are passed to it through environment variables.
        """
        exe_ids = json.loads(
            os.environ.get("DEVTOOLS_AMLRUNTIME_EXE_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )
        group_ids = json.loads(
            os.environ.get("DEVTOOLS_AMLRUNTIME_EVENT_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )

        self._worker_node_runtime().execute(*exe_ids)
        self._worker_node_runtime().execute_group(*group_ids)
