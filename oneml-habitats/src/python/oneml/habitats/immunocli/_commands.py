from argparse import ArgumentParser
from typing import Tuple

from immunodata.cli import CliCommand, ParsedCliRequest

from oneml.habitats.registry._session_registry import PipelineSessionRegistry
from oneml.pipelines.building._remote_execution import NodeRole, RemotePipelineSettings
from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.k8s._executables import IProvideK8sNodeCmds
from oneml.pipelines.settings import PipelineSettingsClient


class OnemlCliCommand(CliCommand):

    command_help = "manage oneml pipelines"
    command_name = "oneml"


class RunOnemlPipelineCommand(CliCommand):

    command_parent = OnemlCliCommand
    command_help = "run a oneml pipeline"
    command_name = "run-pipeline"

    _registry: PipelineSessionRegistry
    _pipeline_settings: PipelineSettingsClient

    def __init__(
        self,
        registry: PipelineSessionRegistry,
        pipeline_settings: PipelineSettingsClient,
    ) -> None:
        self._registry = registry
        self._pipeline_settings = pipeline_settings

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("pipeline")

    def execute(self, request: ParsedCliRequest) -> None:
        self._pipeline_settings.set(RemotePipelineSettings.NODE_ROLE, NodeRole.DRIVER)
        session = self._registry.create_session(request.get("pipeline"))
        session.run()
        print(f"pipeline {request.get('pipeline')} completed")


class RunOnemlPipelineNodeCommand(CliCommand):

    command_parent = OnemlCliCommand
    command_help = "run a oneml pipeline node"
    command_name = "run-pipeline-node"

    _registry: PipelineSessionRegistry
    _pipeline_settings: PipelineSettingsClient

    def __init__(
        self,
        registry: PipelineSessionRegistry,
        pipeline_settings: PipelineSettingsClient,
    ) -> None:
        self._registry = registry
        self._pipeline_settings = pipeline_settings

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("pipeline")
        parser.add_argument("node")

    def execute(self, request: ParsedCliRequest) -> None:
        self._pipeline_settings.set(RemotePipelineSettings.NODE_ROLE, NodeRole.EXECUTOR)
        session = self._registry.create_session(request.get("pipeline"))
        session.run_node(PipelineNode(request.get("node")))
        print(f"pipeline {request.get('pipeline')} node {request.get('node')} completed")


class OnemlPipelineNodeCommandFactory(IProvideK8sNodeCmds):
    def get_k8s_node_cmd(self, node: PipelineNode) -> Tuple[str, ...]:
        raise NotImplementedError()
