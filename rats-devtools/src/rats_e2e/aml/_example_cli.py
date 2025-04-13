import sys
from collections.abc import Iterator
from dataclasses import dataclass
from unittest.mock import patch

import click

from rats import aml as aml
from rats import app_context, apps, cli, logs


@dataclass(frozen=True)
class ExampleContext:
    value: str


class ExampleCliApp(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        """Register our cli commands and run them using click."""
        apps.run(apps.AppBundle(app_plugin=logs.ConfigureApplication))
        cli.create_group(click.Group("rats_e2e.apps"), self)()

    @cli.command()
    def _cli(self) -> None:
        submit_args = ["rats-aml", "submit", "rats_e2e.aml.hello-world"]
        with patch.object(sys, "argv", submit_args):
            apps.run(
                apps.AppBundle(app_plugin=aml.Application),
            )

    @cli.command()
    def _py_api(self) -> None:
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
