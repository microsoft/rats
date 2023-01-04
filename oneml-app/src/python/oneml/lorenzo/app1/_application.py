import logging
from argparse import REMAINDER, ArgumentParser
from contextlib import contextmanager
from typing import Callable, Generator, List, Tuple

from oneml.cli import CliRequest, IApplication
from oneml.lorenzo.app1._context import AppCommand
from oneml.lorenzo.app1._pipeline import App1Pipeline
from oneml.lorenzo.cli import SubParsersAction
from oneml.pipelines.building._remote_execution import NodeRole, RemotePipelineSettings
from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.settings._client import PipelineSettingsClient

logger = logging.getLogger(__name__)
#
# class Bar(IExecutable):
#     def execute(self) -> None:
#         print("woo")
#         storage_account = "ampdatasetsdev01"
#         credential = azure.identity.ManagedIdentityCredential()
#         client = BlobServiceClient(
#             account_url=f"https://{storage_account}.blob.core.windows.net/",
#             credential=credential,
#         )
#         rnd = str(uuid.uuid4())
#         blob = client.get_blob_client("general", f"lolo-prototype/{rnd}.json")
#         blob.upload_blob(json.dumps({"hello": "world"}))
#         print(json.dumps({"hello": "world"}))


class CliRequestStack:

    _stack: List[CliRequest]

    def __init__(self) -> None:
        self._stack = []

    @contextmanager
    def open(self, request: CliRequest) -> Generator[None, None, None]:
        self._stack.append(request)
        try:
            yield
        finally:
            self._stack.pop()

    def get(self) -> CliRequest:
        return self._stack[-1]

    def get_parent(self) -> CliRequest:
        return self._stack[-2]


class App1Application(IApplication):

    _active_command: AppCommand
    _requests: CliRequestStack
    _pipeline: App1Pipeline
    _pipeline_settings: PipelineSettingsClient

    def __init__(
        self,
        requests: CliRequestStack,
        pipeline: App1Pipeline,
        pipeline_settings: PipelineSettingsClient,
    ) -> None:
        self._requests = requests
        self._pipeline = pipeline
        self._active_command = AppCommand.NONE
        self._pipeline_settings = pipeline_settings

    def execute(self) -> None:
        parser = ArgumentParser(
            prog=self._requests.get().entrypoint_basename,
            allow_abbrev=False,
        )
        commands = parser.add_subparsers(title="commands", metavar="", dest="cmd")

        self._add_subcommand(
            action=commands,
            command_name="run-pipeline",
            command_help="run the pipeline (driver)",
            callback=self._run_pipeline,
        )

        self._add_subcommand(
            action=commands,
            command_name="run-pipeline-node",
            command_help="run a single node from the pipeline (executor)",
            callback=self._run_pipeline_node,
        )

        parser.set_defaults(func=lambda _: parser.print_help())

        result = parser.parse_args(self._requests.get().args)
        result.func(vars(result).get("command_args", ()))

    def _run_pipeline(self, args: Tuple[str, ...]) -> None:
        self._active_command = AppCommand.RUN_PIPELINE
        logger.info("Running pipeline!")

        parser = ArgumentParser(
            prog=f"{self._requests.get().entrypoint_basename} run-pipeline",
            allow_abbrev=False,
        )

        parser.add_argument("--image", help="the docker image to use for node execution")

        result = parser.parse_args(args)
        self._pipeline_settings.set(RemotePipelineSettings.DOCKER_IMAGE, result.image)
        self._pipeline_settings.set(RemotePipelineSettings.NODE_ROLE, NodeRole.DRIVER)
        self._pipeline.execute()

    def _run_pipeline_node(self, args: Tuple[str, ...]) -> None:
        self._pipeline_settings.set(RemotePipelineSettings.NODE_ROLE, NodeRole.EXECUTOR)
        print("Running a pipeline node!")
        parser = ArgumentParser(
            prog=f"{self._requests.get().entrypoint_basename} run-pipeline-node",
            allow_abbrev=False,
        )

        parser.add_argument("name", help="pipeline node name to run")

        result = parser.parse_args(args)
        node = PipelineNode(result.name)
        self._pipeline.execute_node(node)

    def _add_subcommand(
        self,
        action: SubParsersAction,
        command_name: str,
        command_help: str,
        callback: Callable[[Tuple[str, ...]], None],
    ) -> None:
        parser = action.add_parser(
            name=command_name,
            # Disabling the help option for subparsers allows us to defer the help ouput
            add_help=False,
            # This allows hyphens to be ignored as options
            # We just need a character that is unlikely to be at the beginning of args
            prefix_chars="%",
            help=command_help,
        )
        parser.add_argument("command_args", nargs=REMAINDER, default=[])
        parser.set_defaults(func=callback)


"""
Notes:
- ArgumentParser(parents=[]) arg allows us to have global arguments?
    - not sure what to pass into parse_args() in this case
- parser.add_argument("subcommand", nargs=REMAINDER, default=[])
    - allows us to say "this command has sub-commands" without having to set them up
"""
