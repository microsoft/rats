from typing import Any

from rats import app_context, apps, cli
from rats.aml import Application


def submit(
    *app_ids: str,
    context: app_context.Collection[Any] = app_context.EMPTY_COLLECTION,
    wait: bool = False,
) -> None:
    """
    Submit an AML job programmatically instead of calling `rats-aml submit`.

    Args:
        app_ids: list of the application to run on the remote aml job as found in pyproject.toml.
        context: context to send to the remote aml job.
        wait: wait for the successful completion of the submitted aml job.
    """
    w = ["--wait"] if wait else []
    cmd = (
        "rats-aml",
        "submit",
        *app_ids,
        "--context",
        app_context.dumps(context),
        *w,
    )
    submitter = apps.AppBundle(
        app_plugin=Application,
        context=apps.StaticContainer(
            apps.static_service(cli.PluginConfigs.ARGV, lambda: cmd),
        ),
    )
    submitter.execute()
