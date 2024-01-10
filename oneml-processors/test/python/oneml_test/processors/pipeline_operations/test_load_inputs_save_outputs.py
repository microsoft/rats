import json
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NamedTuple, cast
from uuid import uuid4

import pytest
from furl import furl

from oneml.app import OnemlApp
from oneml.processors.dag import IProcess
from oneml.processors.io import (
    IReadFromUriPipelineBuilder,
    IWriteToUriPipelineBuilder,
    OnemlProcessorsIoServices,
)
from oneml.processors.registry import ITransformPipeline
from oneml.processors.ux import PipelineRunnerFactory, UPipeline, UPipelineBuilder


class _OperateOutputs(NamedTuple):
    sum: int
    product: int
    statement: str


class _Operate(IProcess):
    def process(self, a: int, b: int, format: str) -> _OperateOutputs:
        sum = a + b
        product = a * b
        statement = format.format(sum=sum, product=product)
        return _OperateOutputs(
            sum=sum,
            product=product,
            statement=statement,
        )


@pytest.fixture(scope="module")
def internal_pipeline_with_inputs_and_outputs() -> UPipeline:
    operate = (
        UPipelineBuilder.task(_Operate)
        .rename_inputs({"a": "inputs_to_load.a", "format": "inputs_to_load.format"})
        .rename_outputs({"sum": "outputs_to_save.sum", "statement": "outputs_to_save.statement"})
    )

    assert set(operate.inputs) == {"b", "inputs_to_load"}
    assert set(operate.inputs.inputs_to_load) == {"a", "format"}
    assert set(operate.outputs) == {"product", "outputs_to_save"}
    assert set(operate.outputs.outputs_to_save) == {"sum", "statement"}

    return operate


@pytest.fixture(scope="module")
def internal_pipeline_with_inputs() -> UPipeline:
    operate = UPipelineBuilder.task(_Operate).rename_inputs(
        {"a": "inputs_to_load.a", "format": "inputs_to_load.format"}
    )

    assert set(operate.inputs) == {"b", "inputs_to_load"}
    assert set(operate.inputs.inputs_to_load) == {"a", "format"}
    assert set(operate.outputs) == {"sum", "product", "statement"}

    return operate


@pytest.fixture(scope="module")
def internal_pipeline_with_outputs() -> UPipeline:
    operate = UPipelineBuilder.task(_Operate).rename_outputs(
        {"sum": "outputs_to_save.sum", "statement": "outputs_to_save.statement"}
    )

    assert set(operate.inputs) == {"a", "b", "format"}
    assert set(operate.outputs) == {"product", "outputs_to_save"}
    assert set(operate.outputs.outputs_to_save) == {"sum", "statement"}

    return operate


class _OperateWithUrisOutputs(NamedTuple):
    sum: int
    product: int
    statement: str
    out_uri1: str
    out_uri2: str


class _OperateWithUris(IProcess):
    def process(
        self, a: int, b: int, format: str, in_uri1: str, output_base_uri: str
    ) -> _OperateWithUrisOutputs:
        sum = a + b
        product = a * b
        statement = format.format(sum=sum, product=product)
        return _OperateWithUrisOutputs(
            sum=sum,
            product=product,
            statement=statement,
            out_uri1=str(furl(output_base_uri) / "out1"),
            out_uri2="out2",
        )


@pytest.fixture(scope="module")
def internal_pipeline_with_inputs_and_outputs_and_uris() -> UPipeline:
    operate = (
        UPipelineBuilder.task(_OperateWithUris)
        .rename_inputs(
            {
                "a": "inputs_to_load.a",
                "format": "inputs_to_load.format",
                "in_uri1": "input_uris.uri1",
            }
        )
        .rename_outputs(
            {
                "sum": "outputs_to_save.sum",
                "statement": "outputs_to_save.statement",
                "out_uri1": "output_uris.uri1",
                "out_uri2": "output_uris.uri2",
            }
        )
    )

    assert set(operate.inputs) == {"b", "inputs_to_load", "input_uris", "output_base_uri"}
    assert set(operate.inputs.inputs_to_load) == {"a", "format"}
    assert set(operate.inputs.input_uris) == {"uri1"}
    assert set(operate.outputs) == {"product", "outputs_to_save", "output_uris"}
    assert set(operate.outputs.outputs_to_save) == {"sum", "statement"}
    assert set(operate.outputs.output_uris) == {"uri1", "uri2"}

    return operate


@pytest.fixture(scope="module")
def tmp_path(tmpdir_factory: Any) -> Iterator[Path]:
    tmp_path = Path(tmpdir_factory.mktemp(".tmp"))
    yield tmp_path
    shutil.rmtree(str(tmp_path))


@pytest.fixture(scope="module")
def write_to_uri_pipeline_builder(app: OnemlApp) -> IWriteToUriPipelineBuilder:
    return app.get_service(OnemlProcessorsIoServices.WRITE_TO_URI_PIPELINE_BUILDER)


@pytest.fixture(scope="module")
def read_from_uri_pipeline_builder(app: OnemlApp) -> IReadFromUriPipelineBuilder:
    return app.get_service(OnemlProcessorsIoServices.READ_FROM_URI_PIPELINE_BUILDER)


@pytest.fixture(scope="module")
def input_path(
    tmp_path: Path,
    write_to_uri_pipeline_builder: IWriteToUriPipelineBuilder,
    pipeline_runner_factory: PipelineRunnerFactory,
) -> Path:
    input_path = tmp_path / str(uuid4())
    write_a = write_to_uri_pipeline_builder.build(
        data_type=int,
        uri=(input_path / "a").as_uri(),
    )
    pipeline_runner_factory(write_a)(dict(data=2))
    write_format = write_to_uri_pipeline_builder.build(
        data_type=str,
        uri=(input_path / "format").as_uri(),
    )
    pipeline_runner_factory(write_format)(
        dict(data="operation result: sum={sum} product={product}")
    )

    return input_path


def get_output_path(tmp_path: Path) -> Path:
    output_path = tmp_path / str(uuid4())
    return output_path


def test_load_inputs_save_outputs_with_inputs_and_outputs(
    internal_pipeline_with_inputs_and_outputs: UPipeline,
    load_inputs_save_outputs: ITransformPipeline[UPipeline, UPipeline],
    pipeline_runner_factory: PipelineRunnerFactory,
    tmp_path: Path,
    input_path: Path,
    read_from_uri_pipeline_builder: IReadFromUriPipelineBuilder,
) -> None:
    pipeline = load_inputs_save_outputs(internal_pipeline_with_inputs_and_outputs)
    output_path = get_output_path(tmp_path)
    expected_inputs = {"b", "output_base_uri"}
    inputs = {
        "b": 3,
        "output_base_uri": output_path.as_uri(),
        "input_uris.a": (input_path / "a").as_uri(),
        "input_uris.format": (input_path / "format").as_uri(),
    }

    assert set(pipeline.inputs) == expected_inputs | {"input_uris"}
    assert set(pipeline.outputs) == {"product", "output_uris"}
    assert set(pipeline.outputs.output_uris) == {"sum", "statement"}

    runner = pipeline_runner_factory(pipeline)
    out = runner(inputs)

    assert out.product == 6

    sum_uri = cast(str, out.output_uris.sum)
    read_sum = read_from_uri_pipeline_builder.build(
        data_type=int,
        uri=sum_uri,
    )
    sum = cast(int, pipeline_runner_factory(read_sum)().data)

    statement_uri = cast(str, out.output_uris.statement)
    read_statement = read_from_uri_pipeline_builder.build(
        data_type=str,
        uri=statement_uri,
    )
    statement = cast(str, pipeline_runner_factory(read_statement)().data)
    assert sum == 5
    assert statement == "operation result: sum=5 product=6"


def test_load_inputs_save_outputs_with_inputs(
    internal_pipeline_with_inputs: UPipeline,
    load_inputs_save_outputs: ITransformPipeline[UPipeline, UPipeline],
    pipeline_runner_factory: PipelineRunnerFactory,
    input_path: Path,
) -> None:
    pipeline = load_inputs_save_outputs(internal_pipeline_with_inputs)
    assert set(pipeline.inputs) == {"b", "input_uris"}
    assert set(pipeline.outputs) == {"sum", "product", "statement"}

    runner = pipeline_runner_factory(pipeline)
    out = runner(
        {
            "b": 3,
            "input_uris.a": (input_path / "a").as_uri(),
            "input_uris.format": (input_path / "format").as_uri(),
        }
    )

    assert out.sum == 5
    assert out.product == 6
    assert out.statement == "operation result: sum=5 product=6"


def test_load_inputs_save_outputs_with_outputs(
    internal_pipeline_with_outputs: UPipeline,
    load_inputs_save_outputs: ITransformPipeline[UPipeline, UPipeline],
    pipeline_runner_factory: PipelineRunnerFactory,
    tmp_path: Path,
    read_from_uri_pipeline_builder: IReadFromUriPipelineBuilder,
) -> None:
    pipeline = load_inputs_save_outputs(internal_pipeline_with_outputs)
    output_path = get_output_path(tmp_path)
    expected_inputs = {"a", "b", "format", "output_base_uri"}
    inputs = {
        "a": 2,
        "b": 3,
        "format": "operation result: sum={sum} product={product}",
        "output_base_uri": output_path.as_uri(),
    }

    assert set(pipeline.inputs) == expected_inputs
    assert set(pipeline.outputs) == {"product", "output_uris"}
    assert set(pipeline.outputs.output_uris) == {"sum", "statement"}

    runner = pipeline_runner_factory(pipeline)
    out = runner(inputs)

    assert out.product == 6

    sum_uri = cast(str, out.output_uris.sum)
    read_sum = read_from_uri_pipeline_builder.build(
        data_type=int,
        uri=sum_uri,
    )
    sum = cast(int, pipeline_runner_factory(read_sum)().data)

    statement_uri = cast(str, out.output_uris.statement)
    read_statement = read_from_uri_pipeline_builder.build(
        data_type=str,
        uri=statement_uri,
    )
    statement = cast(str, pipeline_runner_factory(read_statement)().data)
    assert sum == 5
    assert statement == "operation result: sum=5 product=6"


def test_load_inputs_save_outputs_with_manifest(
    internal_pipeline_with_outputs: UPipeline,
    load_inputs_save_outputs: ITransformPipeline[UPipeline, UPipeline],
    write_manifest: ITransformPipeline[UPipeline, UPipeline],
    pipeline_runner_factory: PipelineRunnerFactory,
    tmp_path: Path,
    read_from_uri_pipeline_builder: IReadFromUriPipelineBuilder,
) -> None:
    pipeline = load_inputs_save_outputs(internal_pipeline_with_outputs)
    pipeline = write_manifest(pipeline)
    output_path = get_output_path(tmp_path)
    expected_inputs = {"a", "b", "format", "output_base_uri"}
    inputs = {
        "a": 2,
        "b": 3,
        "format": "operation result: sum={sum} product={product}",
        "output_base_uri": output_path.as_uri(),
    }

    assert set(pipeline.inputs) == expected_inputs
    assert set(pipeline.outputs) == {"product", "output_uris"}
    assert set(pipeline.outputs.output_uris) == {"manifest"}

    runner = pipeline_runner_factory(pipeline)
    out = runner(inputs)

    assert out.product == 6

    manifest_uri = cast(str, out.output_uris.manifest)
    assert manifest_uri == (output_path / "manifest.json").as_uri()
    with (output_path / "manifest.json").open() as f:
        manifest = json.load(f)
    assert set(manifest) == {"entry_uris"}
    assert set(manifest["entry_uris"]) == {"sum", "statement"}
    sum_uri = (output_path / manifest["entry_uris"]["sum"]).as_uri()
    statement_uri = (output_path / manifest["entry_uris"]["statement"]).as_uri()

    read_sum = read_from_uri_pipeline_builder.build(
        data_type=int,
        uri=sum_uri,
    )
    sum = cast(int, pipeline_runner_factory(read_sum)().data)

    read_statement = read_from_uri_pipeline_builder.build(
        data_type=str,
        uri=statement_uri,
    )
    statement = cast(str, pipeline_runner_factory(read_statement)().data)

    assert sum == 5
    assert statement == "operation result: sum=5 product=6"


def test_load_inputs_save_outputs_with_inputs_and_outputs_and_uris(
    internal_pipeline_with_inputs_and_outputs_and_uris: UPipeline,
    load_inputs_save_outputs: ITransformPipeline[UPipeline, UPipeline],
    pipeline_runner_factory: PipelineRunnerFactory,
    tmp_path: Path,
    input_path: Path,
    read_from_uri_pipeline_builder: IReadFromUriPipelineBuilder,
) -> None:
    pipeline = load_inputs_save_outputs(internal_pipeline_with_inputs_and_outputs_and_uris)
    output_path = get_output_path(tmp_path)
    expected_inputs = {"b", "output_base_uri"}
    inputs: dict[str, Any] = {
        "b": 3,
        "output_base_uri": output_path.as_uri(),
        "input_uris.a": (input_path / "a").as_uri(),
        "input_uris.format": (input_path / "format").as_uri(),
        "input_uris.uri1": "not_used",
    }

    assert set(pipeline.inputs) == expected_inputs | {"input_uris"}
    assert set(pipeline.outputs) == {"product", "output_uris"}
    assert set(pipeline.outputs.output_uris) == {"sum", "statement", "uri1", "uri2"}

    runner = pipeline_runner_factory(pipeline)
    out = runner(inputs)

    assert out.product == 6

    sum_uri = cast(str, out.output_uris.sum)
    read_sum = read_from_uri_pipeline_builder.build(
        data_type=int,
        uri=sum_uri,
    )
    sum = cast(int, pipeline_runner_factory(read_sum)().data)

    statement_uri = cast(str, out.output_uris.statement)
    read_statement = read_from_uri_pipeline_builder.build(
        data_type=str,
        uri=statement_uri,
    )
    statement = cast(str, pipeline_runner_factory(read_statement)().data)
    assert sum == 5
    assert statement == "operation result: sum=5 product=6"
