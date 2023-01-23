import os
import sys

from oneml.cli import CliRequest, build_cli_request
from oneml.cli._request import clean_env
from oneml.lorenzo.app1._di_container import App1DiComponent, App1DiContainer


def main(cli_request: CliRequest) -> None:
    di = App1DiContainer(cli_request)
    di.logging_client().configure_logging()
    requests = di.cli_request_stack()
    app = di.application()
    components = di.pipeline_session_components().session_components()
    components.add_component(App1DiComponent, di)
    with requests.open(cli_request):
        app.execute()


def entrypoint() -> None:
    main(
        build_cli_request(sys.argv[0], tuple(sys.argv[1:]), clean_env(dict(os.environ).copy())),
    )
