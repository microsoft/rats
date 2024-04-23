from abc import abstractmethod
from collections.abc import Mapping
from itertools import chain
from typing import Any, Protocol

import pydot

from rats import apps
from rats.app import RatsApp as LegacyApp
from rats.processors._legacy import dag, ux

from ._pipeline_registry import PipelineRegistryEntry, PipelineRegistryGroups


class IPipelineRunner(Protocol):
    @abstractmethod
    def __call__(self, inputs: Mapping[str, Any] = {}) -> Mapping[str, Any]: ...


class IPipelineRunnerFactory(Protocol):
    @abstractmethod
    def __call__(self, pipeline: ux.UPipeline) -> IPipelineRunner: ...


class IPipelineToDot(Protocol):
    @abstractmethod
    def __call__(self, pipeline: ux.UPipeline, include_optional: bool = True) -> pydot.Dot: ...


class PipelineServiceContainer(apps.AnnotatedContainer):
    _legacy_app: LegacyApp
    _app: apps.Container

    def __init__(self, legacy_app: LegacyApp, app: apps.Container) -> None:
        self._legacy_app = legacy_app
        self._app = app

    @apps.autoid_service
    def pipeline_runner_factory(self) -> IPipelineRunnerFactory:
        return self._legacy_app.get_service(ux.RatsProcessorsUxServices.PIPELINE_RUNNER_FACTORY)

    @apps.autoid_service
    def pipeline_to_dot(self) -> IPipelineToDot:
        return dag._viz.pipeline_to_dot

    @apps.autoid_service
    def executable_pipelines(self) -> tuple[PipelineRegistryEntry, ...]:
        return tuple(chain(*self._app.get_group(PipelineRegistryGroups.EXECUTABLE_PIPELINES)))


class Services:
    PIPELINE_RUNNER_FACTORY = apps.method_service_id(
        PipelineServiceContainer.pipeline_runner_factory
    )
    PIPELINE_TO_DOT = apps.method_service_id(PipelineServiceContainer.pipeline_to_dot)
    EXECUTABLE_PIPELINES = apps.method_service_id(PipelineServiceContainer.executable_pipelines)
