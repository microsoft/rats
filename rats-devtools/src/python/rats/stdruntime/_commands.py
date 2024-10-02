import logging

import click

from rats import apps, cli

logger = logging.getLogger(__name__)


class PluginCommands(cli.Container):
    _standard_runtime: apps.Runtime

    def __init__(self, standard_runtime: apps.Runtime) -> None:
        self._standard_runtime = standard_runtime

    @cli.command()
    @click.option("--exe-id", multiple=True)
    @click.option("--group-id", multiple=True)
    def submit(self, exe_id: tuple[str, ...], group_id: tuple[str, ...]) -> None:
        """Submit a job to the local runtime, in the environment belonging to this cli command."""
        if len(exe_id) == 0 and len(group_id) == 0:
            raise ValueError("No executables or groups were passed to the command")

        exes = [apps.ServiceId[apps.Executable](exe) for exe in exe_id]
        groups = [apps.ServiceId[apps.Executable](group) for group in group_id]
        # we can join these into one job later if needed
        if len(exes):
            self._standard_runtime.execute(*exes)

        if len(groups):
            self._standard_runtime.execute_group(*groups)
