from typing import NamedTuple

import pytest

from oneml.app import OnemlApp
from oneml.processors.pipeline_operations import (
    CollectionToDict,
    DictToCollection,
    DuplicatePipeline,
    ExposeGivenOutputs,
    ITransformPipeline,
    OnemlProcessorsPipelineOperationsServices,
)
from oneml.processors.pipeline_operations._app_plugin import _PrivateServices
from oneml.processors.ux import UPipeline, UPipelineBuilder


@pytest.fixture(scope="package")
def duplicate_pipeline(app: OnemlApp) -> DuplicatePipeline:
    return app.get_service(OnemlProcessorsPipelineOperationsServices.DUPLICATE_PIPELINE)


@pytest.fixture(scope="package")
def expose_given_outputs(app: OnemlApp) -> ExposeGivenOutputs:
    return app.get_service(OnemlProcessorsPipelineOperationsServices.EXPOSE_GIVEN_OUTPUTS)


@pytest.fixture(scope="package")
def load_inputs_save_outputs(app: OnemlApp) -> ITransformPipeline:
    return app.get_service(OnemlProcessorsPipelineOperationsServices.LOAD_INPUTS_SAVE_OUTPUTS)


@pytest.fixture(scope="package")
def expose_pipeline_as_output(app: OnemlApp) -> ITransformPipeline:
    return app.get_service(OnemlProcessorsPipelineOperationsServices.EXPOSE_PIPELINE_AS_OUTPUT)


@pytest.fixture(scope="package")
def write_manifest(app: OnemlApp) -> ITransformPipeline:
    return app.get_service(_PrivateServices.WRITE_MANIFEST)


@pytest.fixture(scope="module")
def collection_to_dict(app: OnemlApp) -> CollectionToDict:
    return app.get_service(OnemlProcessorsPipelineOperationsServices.COLLECTION_TO_DICT)


@pytest.fixture(scope="module")
def dict_to_collection(app: OnemlApp) -> DictToCollection:
    return app.get_service(OnemlProcessorsPipelineOperationsServices.DICT_TO_COLLECTION)


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
    assert set(pl.inputs) == {"u", "v"}
    assert set(pl.in_collections) == {"w", "x"}
    assert set(pl.in_collections.w) == {"a", "b"}
    assert set(pl.in_collections.x) == {"k"}
    assert set(pl.outputs) == {"a", "b"}
    assert set(pl.out_collections) == {"c", "d"}
    assert set(pl.out_collections.c) == {"a", "b"}
    assert set(pl.out_collections.d) == {"a"}
    return pl
