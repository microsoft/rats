import sys
from unittest.mock import patch

import click

from rats import aml as aml
from rats import apps, cli, logs


class ExampleCliApp(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        """Register our cli commands and run them using click."""
        apps.run(apps.AppBundle(app_plugin=logs.ConfigureApplication))
        cli.create_group(click.Group("rats_e2e.apps"), self)()

    @cli.command()
    def _run_all(self) -> None:
        submit_args = ["rats-aml", "submit", "--exe-id", "rats.aml._app:AppServices[hello-world]"]
        with patch.object(sys, "argv", submit_args):
            apps.run(
                apps.AppBundle(
                    app_plugin=aml.Application,
                    context=apps.CompositeContainer(),
                ),
            )
