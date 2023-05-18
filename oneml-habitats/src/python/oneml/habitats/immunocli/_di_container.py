from functools import lru_cache
from pathlib import Path

from immunodata.cli import DiContainerSearch, DiContainerSearchFactory, ILocateDiContainers
from immunodata.core._immunocli import PoetryComponentResourcesPath
from immunodata.core.config.immunoproject import ImmunoProjectConfig
from immunodata.immunocli.next import ImmunocliContainer
from immunodata.resources import ImmunodataResourceLocator

from oneml import habitats
from oneml.habitats.example_diamond._pipelines import DiamondPipelineSession
from oneml.habitats.example_hello_world._builder import HelloWorldPipelineSession
from oneml.habitats.immunocli._commands import (
    OnemlCliCommand,
    RunOnemlPipelineCommand,
    RunOnemlPipelineNodeCommand,
)
from oneml.habitats.immunocli._pipelines_container import OnemlHabitatsPipelinesDiContainer
from oneml.habitats.immunocli._processors_container import OnemlHabitatsProcessorsDiContainer
from oneml.habitats.registry._session_registry import PipelineSessionRegistry
from oneml.pipelines.session import ServicesRegistry


class OnemlHabitatsDiContainer:
    _app: ILocateDiContainers

    def __init__(self, app: ILocateDiContainers):
        self._app = app

    @lru_cache()
    def oneml_command(self) -> OnemlCliCommand:
        return OnemlCliCommand()

    @lru_cache()
    def oneml_run_pipeline_command(self) -> RunOnemlPipelineCommand:
        return RunOnemlPipelineCommand(
            registry=self.session_registry(),
            pipeline_settings=self.pipelines_container().pipeline_settings(),
        )

    @lru_cache()
    def oneml_run_pipeline_node_command(self) -> RunOnemlPipelineNodeCommand:
        return RunOnemlPipelineNodeCommand(
            registry=self.session_registry(),
            pipeline_settings=self.pipelines_container().pipeline_settings(),
        )

    @lru_cache()
    def session_registry(self) -> PipelineSessionRegistry:
        return PipelineSessionRegistry()

    @lru_cache()
    def example_hello_world(self) -> HelloWorldPipelineSession:
        return HelloWorldPipelineSession(
            builder_factory=self.pipelines_container().pipeline_builder_factory(),
            single_port_publisher=self.pipelines_container().single_port_publisher(),
        )

    @lru_cache()
    def example_diamond(self) -> DiamondPipelineSession:
        return DiamondPipelineSession(
            session_provider=self.processors_container().pipeline_session_provider(),
        )

    def services_registry(self) -> ServicesRegistry:
        return self.pipelines_container().services_registry()

    @lru_cache()
    def resources_locator(self) -> ImmunodataResourceLocator:
        return ImmunodataResourceLocator(
            base_path=self._app_resources_path().get_root_path(),
        )

    @lru_cache()
    def _app_resources_path(self) -> PoetryComponentResourcesPath:
        return PoetryComponentResourcesPath(
            project_config=self._project_config(),
            module_path=Path(habitats.__path__[0]),
            component_name="oneml-habitats",
        )

    @lru_cache
    def container_search(self) -> DiContainerSearch:
        return self._di_container_search_factory().get_instance(self)

    def _di_container_search_factory(self) -> DiContainerSearchFactory:
        return self._cli_container().di_container_search_factory()

    def _project_config(self) -> ImmunoProjectConfig:
        return self._cli_container().project_config()

    def _cli_container(self) -> ImmunocliContainer:
        return self._app.find_container(ImmunocliContainer)

    def processors_container(self) -> OnemlHabitatsProcessorsDiContainer:
        return OnemlHabitatsProcessorsDiContainer(
            pipelines_container=self.pipelines_container(),
        )

    def pipelines_container(self) -> OnemlHabitatsPipelinesDiContainer:
        return OnemlHabitatsPipelinesDiContainer()
