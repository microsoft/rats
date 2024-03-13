import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from rats.app import RatsApp
from rats.io import IWriteData, RWDataUri
from rats.processors.io import (
    IGetWriteServicesForType,
    IReadFromUriPipelineBuilder,
    Manifest,
    RatsProcessorsIoServices,
)
from rats.processors.ux import PipelineRunnerFactory


@pytest.fixture(scope="module")
def tmp_path(tmpdir_factory: Any) -> Iterator[Path]:
    tmp_path = Path(tmpdir_factory.mktemp(".tmp"))
    yield tmp_path
    shutil.rmtree(str(tmp_path))


@pytest.fixture(scope="module")
def get_write_services_for_type(app: RatsApp) -> IGetWriteServicesForType:
    return app.get_service(RatsProcessorsIoServices.GET_TYPE_WRITER)


@pytest.fixture(scope="module")
def write_manifest_to_file(
    app: RatsApp, get_write_services_for_type: IGetWriteServicesForType
) -> IWriteData[Manifest]:
    service_id = get_write_services_for_type.get_write_service_ids(Manifest)["file"]
    return app.get_service(service_id)


@pytest.fixture(scope="module")
def write_float_to_file(
    app: RatsApp, get_write_services_for_type: IGetWriteServicesForType
) -> IWriteData[float]:
    service_id = get_write_services_for_type.get_write_service_ids(float)["file"]
    return app.get_service(service_id)


@pytest.fixture(scope="module")
def read_from_uri_pipeline_builder(app: RatsApp) -> IReadFromUriPipelineBuilder:
    return app.get_service(RatsProcessorsIoServices.READ_FROM_URI_PIPELINE_BUILDER)


@pytest.fixture
def a() -> float:
    return 1.0


@pytest.fixture
def b() -> float:
    return 2.0


@pytest.fixture
def manifest_uri(
    tmp_path: Path,
    write_manifest_to_file: IWriteData[Manifest],
    write_float_to_file: IWriteData[float],
    a: float,
    b: float,
) -> str:
    path1 = tmp_path / "path1"
    path2 = tmp_path / "path2"

    manifest_path = path1 / "manifest.json"
    other_manifest_path = path1 / "d" / "manifest.json"
    a_path = path1 / "a.json"
    b_path = path2 / "b.json"

    manifest = Manifest(
        entry_uris={
            "a": "a.json",
            "b": b_path.as_uri(),
            "oa": "d/manifest.json#entry_uris.a",
        }
    )
    other_manifest = Manifest(
        entry_uris={
            "a": a_path.as_uri(),
        }
    )

    write_manifest_to_file.write(RWDataUri(manifest_path.as_uri()), manifest)
    write_manifest_to_file.write(RWDataUri(other_manifest_path.as_uri()), other_manifest)
    write_float_to_file.write(RWDataUri(a_path.as_uri()), a)
    write_float_to_file.write(RWDataUri(b_path.as_uri()), b)

    return manifest_path.as_uri()


def test_read_manifest(
    manifest_uri: str,
    read_from_uri_pipeline_builder: IReadFromUriPipelineBuilder,
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    pipeline = read_from_uri_pipeline_builder.build(Manifest, uri=manifest_uri)
    pipeline_runner = pipeline_runner_factory(pipeline)
    output = pipeline_runner()
    manifest1 = output.data
    assert output.data["entry_uris"]["a"] == "a.json"
    assert "b" in output.data["entry_uris"]

    pipeline = read_from_uri_pipeline_builder.build(Manifest)
    pipeline_runner = pipeline_runner_factory(pipeline)
    output = pipeline_runner(dict(uri=manifest_uri))
    manifest2 = output.data
    assert manifest1 == manifest2


def test_read_when_manifest_points_to_relative_path(
    manifest_uri: str,
    read_from_uri_pipeline_builder: IReadFromUriPipelineBuilder,
    pipeline_runner_factory: PipelineRunnerFactory,
    a: float,
) -> None:
    uri = manifest_uri + "#entry_uris.a"
    pipeline = read_from_uri_pipeline_builder.build(float, uri=uri)
    pipeline_runner = pipeline_runner_factory(pipeline)
    output = pipeline_runner()
    assert isinstance(output.data, float)
    assert output.data == a


def test_read_when_manifest_points_to_absolute_uri(
    manifest_uri: str,
    read_from_uri_pipeline_builder: IReadFromUriPipelineBuilder,
    pipeline_runner_factory: PipelineRunnerFactory,
    b: float,
) -> None:
    uri = manifest_uri + "#entry_uris.b"
    pipeline = read_from_uri_pipeline_builder.build(float, uri=uri)
    pipeline_runner = pipeline_runner_factory(pipeline)
    output = pipeline_runner()
    assert isinstance(output.data, float)
    assert output.data == b


def test_read_with_multiple_manifest_hops(
    manifest_uri: str,
    read_from_uri_pipeline_builder: IReadFromUriPipelineBuilder,
    pipeline_runner_factory: PipelineRunnerFactory,
    a: float,
) -> None:
    uri = manifest_uri + "#entry_uris.oa"
    pipeline = read_from_uri_pipeline_builder.build(float, uri=uri)
    pipeline_runner = pipeline_runner_factory(pipeline)
    output = pipeline_runner()
    assert isinstance(output.data, float)
    assert output.data == a
