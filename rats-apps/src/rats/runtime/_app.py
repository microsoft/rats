from __future__ import annotations

import json
import logging
import sys
from collections.abc import Iterator
from functools import cache
from importlib import metadata
from importlib.metadata import EntryPoint
from pathlib import Path
from typing import Any, final

import click
import yaml

from rats import app_context, apps, cli, logs

from ._request import DuplicateRequestError, Request, RequestNotFoundError

logger = logging.getLogger(__name__)


@apps.autoscope
class AppServices:
    """Services used by the `rats.runtime.Application` cli command."""

    CONTEXT = apps.ServiceId[app_context.Collection[Any]]("app-ctx-collection.config")
    """
    [rats.app_context.Collection][] available in the application run using `rats-runtime run`.

    ```python
    from rats import apps, runtime


    class Application(apps.AppContainer, apps.PluginMixin):
        def execute(self) -> None:
            context = self._app.get(runtime.AppConfigs.CONTEXT)
            print("loaded context:")
            for item in context_collection.items:
                print(f"{item.service_id} -> {item.values}")
    ```
    """
    REQUEST = apps.ServiceId[Request]("runtime-details-client")
    """
    The request information, available after the call to [rats.runtime.Application.execute][].
    """


@final
class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    """
    The `rats-runtime` cli application.

    ```bash
    $ rats-runtime --help
    Usage: rats-runtime [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      list  List all the exes and groups that are configured to run with `rats-
            runtime run`.
      run   Run one or more apps, adding an optional additional context.
    ```
    """

    _request: Request | None = None

    def execute(self) -> None:
        """Runs the `rats-runtime` cli."""
        argv = self._app.get(cli.PluginConfigs.ARGV)
        cli.create_group(click.Group("rats-runtime"), self).main(
            args=argv[1:],
            prog_name=Path(argv[0]).name,
            auto_envvar_prefix="RATS_RUNTIME",
            # don't end the process
            standalone_mode=False,
        )

    @cli.command()
    def _list(self) -> None:
        """List all the exes and groups that are configured to run with `rats-runtime run`."""
        for entry in self._get_app_entrypoints():
            click.echo(entry.name)

    @cli.command()
    @click.argument("app-ids", nargs=-1)
    @click.option("--context", default="{}")
    @click.option("--context-file")
    def _run(self, app_ids: tuple[str, ...], context: str, context_file: str | None) -> None:
        """Run one or more apps, adding an optional additional context."""
        if self._request is not None:
            print(self._request)
            raise DuplicateRequestError()

        ctx_collection = app_context.loads(context)
        if context_file:
            p = Path(context_file)
            if not p.is_file():
                raise RuntimeError(f"context file not found: {context_file}")

            data = yaml.safe_load(p.read_text())
            ctx_collection = ctx_collection.merge(app_context.loads(json.dumps(data)))

        self._request = Request(
            app_ids=app_ids,
            context=ctx_collection,
        )

        def _load_app(name: str, ctx: app_context.Collection[Any]) -> apps.AppContainer:
            return apps.AppBundle(
                app_plugin=self._find_app(name),
                context=apps.StaticContainer(
                    apps.StaticProvider(
                        namespace=apps.ProviderNamespaces.SERVICES,
                        service_id=AppServices.CONTEXT,
                        call=lambda: ctx,
                    ),
                ),
            )

        if len(app_ids) == 0:
            logger.warning("No applications were passed to the command")

        for app_id in app_ids:
            app = _load_app(app_id, ctx_collection)
            app.execute()

    def _find_app(self, name: str) -> type[apps.AppContainer]:
        for e in self._get_app_entrypoints():
            if e.name == name:
                return e.load()

        raise RuntimeError(f"rats app-id not found: {name}")

    @cache  # noqa: B019
    def _get_app_entrypoints(self) -> Iterator[EntryPoint]:
        yield from metadata.entry_points(group="rats.runtime.apps")

    @apps.service(AppServices.REQUEST)
    def _request_provider(self) -> Request:
        if self._request is None:
            raise RequestNotFoundError()

        return self._request

    @apps.container()
    def _plugins(self) -> apps.Container:
        return cli.PluginContainer(self._app)


def main() -> None:
    """Main entry-point to the `rats-runtime` cli command."""
    try:
        apps.run_plugin(logs.ConfigureApplication)
        apps.run_plugin(Application)
    except click.exceptions.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
