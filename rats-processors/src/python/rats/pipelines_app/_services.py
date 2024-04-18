from abc import abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, Protocol
from uuid import uuid4

import pydot

from rats import apps
from rats.app import RatsApp as LegacyApp
from rats.processors import dag, ux

from ._combiner import IPipelineCombiner


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
    def pipeline_combiner(self) -> IPipelineCombiner:
        def combiner(
            pipelines: Sequence[ux.UPipeline],
            name: str | None = None,
            dependencies: Sequence[ux.DependencyOp[Any]] | None = None,
            inputs: ux.UserInput | None = None,
            outputs: ux.UserOutput | None = None,
        ) -> ux.UPipeline:
            name = name or uuid4().hex
            return ux.CombinedPipeline(
                pipelines=pipelines,
                name=name,
                dependencies=dependencies,
                inputs=inputs,
                outputs=outputs,
            )

        return combiner

    @apps.autoid_service
    def pipeline_runner_factory(self) -> IPipelineRunnerFactory:
        return self._legacy_app.get_service(ux.RatsProcessorsUxServices.PIPELINE_RUNNER_FACTORY)

    @apps.autoid_service
    def pipeline_to_dot(self) -> IPipelineToDot:
        return dag._viz.pipeline_to_dot


class PipelineServices:
    PIPELINE_COMBINER = apps.method_service_id(PipelineServiceContainer.pipeline_combiner)
    PIPELINE_RUNNER_FACTORY = apps.method_service_id(
        PipelineServiceContainer.pipeline_runner_factory
    )
    PIPELINE_TO_DOT = apps.method_service_id(PipelineServiceContainer.pipeline_to_dot)
