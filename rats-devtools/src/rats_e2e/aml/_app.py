from collections.abc import Iterator

import click

from rats import aml as aml
from rats import app_context, apps, cli, logs

from ._example_job import ExampleData, JobServices


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        """Register our cli commands and run them using click."""
        apps.run(apps.AppBundle(app_plugin=logs.ConfigureApplication))
        cli.create_group(click.Group("rats-e2e.apps"), self)()

    @cli.command()
    def _example_job(self) -> None:
        def envs() -> Iterator[dict[str, str]]:
            yield {"RATS_AML_E2E_EXAMPLE": "this env is attached to the remote job"}

        aml.submit(
            "rats_e2e.aml.hello-world",
            container_plugin=lambda app: apps.StaticContainer(
                apps.static_group(aml.AppConfigs.CLI_ENVS, envs)
            ),
            context=app_context.Collection.make(
                app_context.Context.make(
                    JobServices.EXAMPLE_DATA,
                    ExampleData("example data name", "example data value"),
                    ExampleData("another example data name", "another example data value"),
                ),
            ),
            wait=True,
        )


def main() -> None:
    apps.run_plugin(Application)
