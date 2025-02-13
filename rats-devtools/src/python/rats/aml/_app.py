import logging

import click
from rats import apps, cli, logs, projects

logger = logging.getLogger(__name__)


@apps.autoscope
class AppServices:
    CLI_CONTAINERS = apps.ServiceId[cli.Container]("cli-containers")
    """
    Service group to be used for registering [rats.cli.Container][] instances.
    """


class Application(apps.AppContainer, apps.PluginMixin):
    def execute(self) -> None:
        cli.create_group(
            click.Group("rats-aml"),
            cli.CompositeContainer(*self._app.get_group(AppServices.CLI_CONTAINERS)),
        )()

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            apps.PythonEntryPointContainer(self._app, "rats.aml"),
            projects.PluginContainer(self._app),
        )


def main() -> None:
    """
    Main entry-point to the `rats-aml` cli command.
    """
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
