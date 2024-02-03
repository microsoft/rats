import logging
import os
import sys

from oneml.adocli._cli import RawCliRequest
from oneml.adocli._di_container import AdocliDiContainer
from oneml.logging import PackageLogLevel

logger = logging.getLogger(__name__)


def main(argv: tuple[str, ...]) -> None:
    di_container = AdocliDiContainer(RawCliRequest(
        argv=argv,
        environ=dict(os.environ),
    ))
    logging_client = di_container.logging_client()
    logging_client.set_log_levels(
        PackageLogLevel(package="azure", level="INFO"),
        PackageLogLevel(package="msrest", level="INFO"),
        PackageLogLevel(package="urllib3", level="INFO"),
    )
    logging_client.apply_config()
    app = di_container.cli_app()
    app.execute()


def entrypoint() -> None:
    main(tuple(sys.argv))


if __name__ == "__main__":
    main(tuple(["adocli", "update-goalie-sprint"]))
