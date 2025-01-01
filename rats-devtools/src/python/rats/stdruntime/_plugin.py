import logging
from collections.abc import Iterator

import click

from rats import apps, cli
from rats import devtools as devtools

logger = logging.getLogger(__name__)


@apps.autoscope
class PluginServices:
    STANDARD_RUNTIME = apps.ServiceId[apps.StandardRuntime]("std-runtime")


class PluginContainer(apps.Container, apps.PluginMixin, cli.Container):
    @cli.command()
    @click.option("--exe-id", multiple=True)
    @click.option("--group-id", multiple=True)
    def submit(self, exe_id: tuple[str, ...], group_id: tuple[str, ...]) -> None:
        """Submit a job to the local runtime, in the environment belonging to this cli command."""
        if len(exe_id) == 0 and len(group_id) == 0:
            logger.warning("No executables or groups were passed to the command")

        runtime = self._app.get(PluginServices.STANDARD_RUNTIME)

        exes = [apps.ServiceId[apps.Executable](exe) for exe in exe_id]
        groups = [apps.ServiceId[apps.Executable](group) for group in group_id]
        # we can join these into one job later if needed
        if len(exes):
            runtime.execute(*exes)

        if len(groups):
            runtime.execute_group(*groups)

    @apps.group(devtools.AppServices.ON_REGISTER)
    def _runtime_cli(self) -> Iterator[apps.Executable]:
        yield apps.App(
            lambda: cli.attach(
                self._app.get(devtools.AppServices.MAIN_CLICK),
                cli.create_group(
                    click.Group(
                        "std-runtime",
                        help="submit executables and events to the in-thread runtime.",
                    ),
                    self,
                ),
            )
        )

    @apps.service(PluginServices.STANDARD_RUNTIME)
    def _std_runtime(self) -> apps.StandardRuntime:
        return apps.StandardRuntime(self._app)
