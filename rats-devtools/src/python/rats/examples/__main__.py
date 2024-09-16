"""rats-examples provides a tiny cli to run a handful of example executables (apps)."""

import json
import logging
import os

from rats import apps, logs
from rats.examples import PluginServices

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    app = apps.SimpleApplication(
        "rats.apps.plugins",
        "rats.examples.plugins",
    )
    app.execute_group(logs.PluginServices.EVENTS.CONFIGURE_LOGGING)
    exe_ids = [
        apps.ServiceId[apps.Executable](**x)
        for x in json.loads(os.environ.get("DEVTOOLS_EXE_IDS", "[]"))
    ]
    event_ids = [
        apps.ServiceId[apps.Executable](**x)
        for x in json.loads(os.environ.get("DEVTOOLS_EVENT_IDS", "[]"))
    ]

    if len(exe_ids) + len(event_ids) > 0:
        logger.info(f"running ids provided by env variables: {exe_ids + event_ids}")
        app.execute(*exe_ids)
        app.execute_group(*event_ids)
    else:
        logger.info("running default examples")
        ids = [
            PluginServices.PING,
            PluginServices.PONG,
            PluginServices.PING,
            PluginServices.PONG,
        ]
        print(f"executing: {ids}")
        app.execute(*ids)
