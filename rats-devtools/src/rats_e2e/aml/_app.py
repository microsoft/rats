from collections.abc import Iterator
from dataclasses import dataclass

import click

from rats import aml as aml
from rats import app_context, apps, cli, logs


@dataclass(frozen=True)
class ExampleContext:
    value: str


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        """Register our cli commands and run them using click."""
        apps.run(apps.AppBundle(app_plugin=logs.ConfigureApplication))
        cli.create_group(click.Group("rats_e2e.apps"), self)()

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
                    apps.ServiceId[ExampleContext]("e2e-test-group"),
                    ExampleContext("this is an example value"),
                ),
            ),
            wait=True,
        )


def main() -> None:
    apps.run_plugin(Application)
