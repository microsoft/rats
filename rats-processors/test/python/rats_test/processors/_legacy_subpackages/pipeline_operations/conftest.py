from typing import NamedTuple

import pytest

from rats.app import RatsApp
from rats.processors._legacy_subpackages.pipeline_operations import (
    CollectionToDict,
    DictToCollection,
    DuplicatePipeline,
    ExposeGivenOutputs,
    RatsProcessorsPipelineOperationsServices,
)
from rats.processors._legacy_subpackages.pipeline_operations._app_plugin import _PrivateServices
from rats.processors._legacy_subpackages.registry import ITransformPipeline
from rats.processors._legacy_subpackages.ux import UPipeline, UPipelineBuilder


@pytest.fixture(scope="package")
def duplicate_pipeline(app: RatsApp) -> DuplicatePipeline:
    return app.get_service(RatsProcessorsPipelineOperationsServices.DUPLICATE_PIPELINE)


@pytest.fixture(scope="package")
def expose_given_outputs(app: RatsApp) -> ExposeGivenOutputs:
    return app.get_service(RatsProcessorsPipelineOperationsServices.EXPOSE_GIVEN_OUTPUTS)


@pytest.fixture(scope="package")
def load_inputs_save_outputs(app: RatsApp) -> ITransformPipeline[UPipeline, UPipeline]:
    return app.get_service(RatsProcessorsPipelineOperationsServices.LOAD_INPUTS_SAVE_OUTPUTS)


@pytest.fixture(scope="package")
def expose_pipeline_as_output(app: RatsApp) -> ITransformPipeline[UPipeline, UPipeline]:
    return app.get_service(RatsProcessorsPipelineOperationsServices.EXPOSE_PIPELINE_AS_OUTPUT)


@pytest.fixture(scope="package")
def write_manifest(app: RatsApp) -> ITransformPipeline[UPipeline, UPipeline]:
    return app.get_service(_PrivateServices.WRITE_MANIFEST)


@pytest.fixture(scope="module")
def collection_to_dict(app: RatsApp) -> CollectionToDict:
    return app.get_service(RatsProcessorsPipelineOperationsServices.COLLECTION_TO_DICT)


@pytest.fixture(scope="module")
def dict_to_collection(app: RatsApp) -> DictToCollection:
    return app.get_service(RatsProcessorsPipelineOperationsServices.DICT_TO_COLLECTION)


class _ProcessorOutput(NamedTuple):
    a: float
    b: str
    c_a: float
    c_b: str
    d_a: float


class _Processor:
    def process(self, u: str, v: int, w_a: int, w_b: int, x_k: int) -> _ProcessorOutput:
        raise NotImplementedError()


@pytest.fixture(scope="module")
def pipeline_for_tests() -> UPipeline:
    pl = (
        UPipelineBuilder.task(_Processor)
        .rename_inputs({"w_a": "w.a", "w_b": "w.b", "x_k": "x.k"})
        .rename_outputs({"c_a": "c.a", "c_b": "c.b", "d_a": "d.a"})
    )
    assert set(pl.inputs) == {"u", "v", "w", "x"}
    assert set(pl.inputs.w) == {"a", "b"}
    assert set(pl.inputs.x) == {"k"}
    assert set(pl.outputs) == {"a", "b", "c", "d"}
    assert set(pl.outputs.c) == {"a", "b"}
    assert set(pl.outputs.d) == {"a"}
    return pl
