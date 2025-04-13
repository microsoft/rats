import sys
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
        aml.submit(
            "rats_e2e.aml.hello-world",
            context=app_context.Collection.make(
                app_context.Context.make(
                    apps.ServiceId[ExampleContext]("e2e-test-group"),
                    ExampleContext("this is an example value"),
                ),
            ),
            wait=True,
        )
