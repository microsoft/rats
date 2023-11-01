import re
from typing import NamedTuple
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from immunodata.datasets import DatasetClient, IDatasetClient
from immunodata.datasets.storage import DatasetMemoryStorage

from oneml.app import OnemlApp
from oneml.habitats.pipeline_operations import OnemlHabitatsPipelineOperationsServices
from oneml.habitats.pipeline_operations._datasets._ampds_uri_service import (
    ComposeAmpdsUriFromCommit,
    ParseAmpdsUriForRead,
    ParseAmpdsUriForWrite,
)
from oneml.habitats.pipeline_operations._datasets._prepare_and_publish_service import (
    DatasetPrepareAndPublishService,
    IDatasetPrepareAndPublishService,
)
from oneml.habitats.pipeline_operations._datasets._publish_service import DatasetPublishService
from oneml.habitats.pipeline_operations._datasets._read_commit_service import (
    DatasetReadCommitService,
    DatasetReadSpecifications,
)
from oneml.habitats.pipeline_operations._datasets._utils import extend_uri_path
from oneml.habitats.pipeline_operations._datasets._write_specifications import (
    DatasetWriteSpecifications,
)
from oneml.habitats.pipeline_operations._datasets._write_storage_location_service import (
    IDatasetWriteStorageLocationService,
)
from oneml.habitats.pipeline_operations._publish_outputs_as_dataset import PublishOutputsAsDataset
from oneml.processors.pipeline_operations import CollectionToDict, DictToCollection
from oneml.processors.utils import frozendict
from oneml.processors.ux import PipelineRunnerFactory, UPipeline, UPipelineBuilder
from oneml.services import ServiceId


class MockDatasetWriteStorageLocationService(IDatasetWriteStorageLocationService):
    def get_storage_uri(self, dataset: DatasetWriteSpecifications) -> str:
        uuid = str(uuid4())
        return f"mock://mockloc/{dataset.name}/{dataset.namespace}/{dataset.partition}/{uuid}"


@pytest.fixture
def write_storage_location_service() -> IDatasetWriteStorageLocationService:
    return MockDatasetWriteStorageLocationService()


@pytest.fixture
def dataset_client() -> IDatasetClient:
    return DatasetClient(DatasetMemoryStorage())


@pytest.fixture
def dataset_read_commit_service(dataset_client: IDatasetClient) -> DatasetReadCommitService:
    return DatasetReadCommitService(dataset_client)


@pytest.fixture
def dataset_publish_service(dataset_client: IDatasetClient) -> DatasetPublishService:
    return DatasetPublishService(dataset_client)


@pytest.fixture
def dataset_prepare_and_publish_service(
    dataset_read_commit_service: DatasetReadCommitService,
    write_storage_location_service: IDatasetWriteStorageLocationService,
    dataset_publish_service: DatasetPublishService,
) -> DatasetPrepareAndPublishService:
    return DatasetPrepareAndPublishService(
        parse_ampds_uri_for_read=ParseAmpdsUriForRead(),
        parse_ampds_uri_for_write=ParseAmpdsUriForWrite(),
        dataset_read_commit=dataset_read_commit_service,
        dataset_write_storage_location=write_storage_location_service,
        dataset_publish=dataset_publish_service,
        compose_ampds_uri_from_commit=ComposeAmpdsUriFromCommit(),
    )


@pytest.fixture
def prepare_and_publish_service_id(
    app: OnemlApp, dataset_prepare_and_publish_service: DatasetPrepareAndPublishService
) -> ServiceId[IDatasetPrepareAndPublishService]:
    def service_provider() -> DatasetPrepareAndPublishService:
        return dataset_prepare_and_publish_service

    service_id = ServiceId[IDatasetPrepareAndPublishService](str(uuid4()))
    app.add_service(service_id, service_provider)
    return service_id


@pytest.fixture
def publish_outputs_as_dataset(
    prepare_and_publish_service_id: ServiceId[IDatasetPrepareAndPublishService],
    dataset_client: IDatasetClient,
) -> PublishOutputsAsDataset:
    return PublishOutputsAsDataset(
        collection_to_dict=CollectionToDict(),
        dict_to_collection=DictToCollection(),
        dataset_prepare_and_publish_service_id=prepare_and_publish_service_id,
    )


class VerificationProcessor1Outputs(NamedTuple):
    output_uri_1: str
    output_uri_2: str
    output_uri_3: str
    a_a: int
    a_b: str
    c: int


class VerificationProcessor1:
    _expected_input_uri_1_pattern: str
    _expected_input_uri_2_pattern: str
    _expected_output_base_uri_pattern: str

    def __init__(
        self,
        expected_input_uri_1_pattern: str,
        expected_input_uri_2_pattern: str,
        expected_output_base_uri_pattern: str,
    ) -> None:
        self._expected_input_uri_1_pattern = expected_input_uri_1_pattern
        self._expected_input_uri_2_pattern = expected_input_uri_2_pattern
        self._expected_output_base_uri_pattern = expected_output_base_uri_pattern

    def process(
        self,
        input_uri_1: str,
        input_uri_2: str,
        output_base_uri: str,
        x_a: float,
        x_b: str,
        y: float,
    ) -> VerificationProcessor1Outputs:
        assert re.match(self._expected_input_uri_1_pattern, input_uri_1)
        assert re.match(self._expected_input_uri_2_pattern, input_uri_2)
        assert re.match(self._expected_output_base_uri_pattern, output_base_uri)
        return VerificationProcessor1Outputs(
            output_uri_1=extend_uri_path(output_base_uri, "output_1"),
            output_uri_2=extend_uri_path(output_base_uri, "output_2"),
            output_uri_3=extend_uri_path(output_base_uri, "output_3"),
            a_a=10,
            a_b="s",
            c=100,
        )


def get_verification_pipeline_1(
    expected_input_uri_1_pattern: str,
    expected_input_uri_2_pattern: str,
    expected_output_base_uri_pattern: str,
) -> UPipeline:
    task = UPipelineBuilder.task(
        VerificationProcessor1,
        config=frozendict(
            expected_input_uri_1_pattern=expected_input_uri_1_pattern,
            expected_input_uri_2_pattern=expected_input_uri_2_pattern,
            expected_output_base_uri_pattern=expected_output_base_uri_pattern,
        ),
    )
    pl = task.rename_inputs(
        dict(
            input_uri_1="input_uris.i1",
            input_uri_2="input_uris.i2",
            x_a="x.a",
            x_b="x.b",
        )
    ).rename_outputs(
        dict(
            output_uri_1="output_uris.o1",
            output_uri_2="output_uris.o2",
            output_uri_3="output_uris.o3",
            a_a="a.a",
            a_b="a.b",
        )
    )
    assert set(pl.inputs) == {"output_base_uri", "y", "input_uris", "x"}
    assert set(pl.inputs.input_uris) == {"i1", "i2"}
    assert set(pl.inputs.x) == {"a", "b"}
    assert set(pl.outputs) == {"c", "output_uris", "a"}
    assert set(pl.outputs.output_uris) == {"o1", "o2", "o3"}
    assert set(pl.outputs.a) == {"a", "b"}
    return pl


def test_publish_outputs_as_datasets_pipeline_interface(
    publish_outputs_as_dataset: PublishOutputsAsDataset,
) -> None:
    # we're not going to run the verification processor, so we don't care about the patterns
    pl = get_verification_pipeline_1(
        expected_input_uri_1_pattern="",
        expected_input_uri_2_pattern="",
        expected_output_base_uri_pattern="",
    )
    pl = publish_outputs_as_dataset(pl)
    assert set(pl.inputs) == {"output_base_uri", "y", "allow_overwrite", "input_uris", "x"}
    assert set(pl.inputs.input_uris) == {"i1", "i2"}
    assert set(pl.inputs.x) == {"a", "b"}
    assert set(pl.outputs) == {"c", "output_uris", "a"}


def test_publish_outputs_as_dataset_with_no_datasets(
    publish_outputs_as_dataset: PublishOutputsAsDataset,
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    input_uri_1 = "file:///path1/to/file1"
    expected_resolved_pattern_1 = "^file:///path1/to/file1$"
    input_uri_2 = "file:///path1/to/file2"
    expected_resolved_pattern_2 = "^file:///path1/to/file2$"
    output_base_uri = "file:///path_to_output/under_here"
    expected_resolved_output_base_uri_pattern = "^file:///path_to_output/under_here$"
    pl = get_verification_pipeline_1(
        expected_input_uri_1_pattern=expected_resolved_pattern_1,
        expected_input_uri_2_pattern=expected_resolved_pattern_2,
        expected_output_base_uri_pattern=expected_resolved_output_base_uri_pattern,
    )
    pl = publish_outputs_as_dataset(pl)
    inputs = {
        "output_base_uri": output_base_uri,
        "y": 3.4,
        "allow_overwrite": True,
        "input_uris.i1": input_uri_1,
        "input_uris.i2": input_uri_2,
        "x.a": 1.0,
        "x.b": "s",
    }
    runner = pipeline_runner_factory(pl)
    outputs = runner(inputs)
    assert outputs.output_uris.o1 == extend_uri_path(output_base_uri, "output_1")
    assert outputs.output_uris.o2 == extend_uri_path(output_base_uri, "output_2")
    assert outputs.output_uris.o3 == extend_uri_path(output_base_uri, "output_3")
    assert outputs.a.a == 10
    assert outputs.a.b == "s"
    assert outputs.c == 100


def test_publish_outputs_as_dataset_with_datasets(
    dataset_read_commit_service: DatasetReadCommitService,
    publish_outputs_as_dataset: PublishOutputsAsDataset,
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    # case 1: inputs are not datasets, output is
    # published commit should have no parents
    input_uri_1 = "file:///path1/to/file1"
    expected_resolved_pattern_1 = "^file:///path1/to/file1$"
    input_uri_2 = "file:///path1/to/file2"
    expected_resolved_pattern_2 = "^file:///path1/to/file2$"
    output_base_uri = "ampds://datASet1/path/to/folder?partition=2022-02-23&namespace=namespace1"
    expected_resolved_output_base_uri_pattern = (
        "^mock://mockloc/datASet1/namespace1/2022-02-23/[^/]+/path/to/folder$"
    )

    pl = get_verification_pipeline_1(
        expected_input_uri_1_pattern=expected_resolved_pattern_1,
        expected_input_uri_2_pattern=expected_resolved_pattern_2,
        expected_output_base_uri_pattern=expected_resolved_output_base_uri_pattern,
    )
    pl = publish_outputs_as_dataset(pl)
    inputs = {
        "output_base_uri": output_base_uri,
        "y": 3.4,
        "allow_overwrite": False,
        "input_uris.i1": input_uri_1,
        "input_uris.i2": input_uri_2,
        "x.a": 1.0,
        "x.b": "s",
    }
    runner = pipeline_runner_factory(pl)
    outputs = runner(inputs)

    f1 = urlparse(outputs.output_uris.o1)
    f2 = urlparse(outputs.output_uris.o2)
    f3 = urlparse(outputs.output_uris.o3)
    f1qs = parse_qs(f1.query)
    f2qs = parse_qs(f2.query)
    f3qs = parse_qs(f3.query)

    assert f1.path == "/path/to/folder/output_1"
    assert f2.path == "/path/to/folder/output_2"
    assert f3.path == "/path/to/folder/output_3"
    assert f1.scheme == "ampds"
    assert f2.scheme == "ampds"
    assert f3.scheme == "ampds"
    assert f1.netloc == "datASet1"
    assert f2.netloc == "datASet1"
    assert f3.netloc == "datASet1"
    assert f1qs["namespace"] == ["namespace1"]
    assert f2qs["namespace"] == ["namespace1"]
    assert f3qs["namespace"] == ["namespace1"]
    assert f1qs["partition"] == ["2022-02-23"]
    assert f2qs["partition"] == ["2022-02-23"]
    assert f3qs["partition"] == ["2022-02-23"]
    assert len(f1qs["commit_id"]) == 1
    commit_id = f1qs["commit_id"][0]
    assert f2qs["commit_id"] == [commit_id]
    assert f3qs["commit_id"] == [commit_id]

    assert outputs.a.a == 10
    assert outputs.a.b == "s"
    assert outputs.c == 100

    commit1 = dataset_read_commit_service.get_commit(
        DatasetReadSpecifications(
            name="datASet1",
            namespace="namespace1",
            partition="2022-02-23",
            path_in_dataset="",
            snapshot=None,
            commit_id=commit_id,
        )
    )
    assert commit1 is not None
    assert commit1.id == commit_id
    assert commit1.dataset_name == "datASet1"
    assert commit1.dataset_namespace == "namespace1"
    assert commit1.partition == "2022-02-23"
    assert commit1.parent_commits == tuple()
    assert re.match("^mock://mockloc/datASet1/namespace1/2022-02-23/[^/]+$", commit1.uri)

    # case 2, use the dataset published above as input, publish another dataset
    # output commit should have a single parent, the commit of the first dataset.
    input_uri_1 = (
        "ampds://datASet1/path/to/folder/output_1?partition=2022-02-23&namespace=namespace1"
    )
    expected_resolved_pattern_1 = (
        "^mock://mockloc/datASet1/namespace1/2022-02-23/[^/]+/path/to/folder/output_1$"
    )
    input_uri_2 = (
        "ampds://datASet1/path/to/folder/output_2?partition=2022-02-23&namespace=namespace1"
    )
    expected_resolved_pattern_2 = (
        "^mock://mockloc/datASet1/namespace1/2022-02-23/[^/]+/path/to/folder/output_2$"
    )
    output_base_uri = "ampds://dataset2?partition=2022-02-23&namespace=namespace1"
    expected_resolved_output_base_uri_pattern = (
        "^mock://mockloc/dataset2/namespace1/2022-02-23/[^/]+$"
    )

    pl = get_verification_pipeline_1(
        expected_input_uri_1_pattern=expected_resolved_pattern_1,
        expected_input_uri_2_pattern=expected_resolved_pattern_2,
        expected_output_base_uri_pattern=expected_resolved_output_base_uri_pattern,
    )
    pl = publish_outputs_as_dataset(pl)
    inputs = {
        "output_base_uri": output_base_uri,
        "y": 3.4,
        "allow_overwrite": False,
        "input_uris.i1": input_uri_1,
        "input_uris.i2": input_uri_2,
        "x.a": 1.0,
        "x.b": "s",
    }
    runner = pipeline_runner_factory(pl)
    outputs = runner(inputs)

    f1 = urlparse(outputs.output_uris.o1)
    f2 = urlparse(outputs.output_uris.o2)
    f3 = urlparse(outputs.output_uris.o3)
    f1qs = parse_qs(f1.query)
    f2qs = parse_qs(f2.query)
    f3qs = parse_qs(f3.query)

    assert f1.path == "/output_1"
    assert f2.path == "/output_2"
    assert f3.path == "/output_3"
    assert f1.scheme == "ampds"
    assert f2.scheme == "ampds"
    assert f3.scheme == "ampds"
    assert f1.netloc == "dataset2"
    assert f2.netloc == "dataset2"
    assert f3.netloc == "dataset2"
    assert f1qs["namespace"] == ["namespace1"]
    assert f2qs["namespace"] == ["namespace1"]
    assert f3qs["namespace"] == ["namespace1"]
    assert f1qs["partition"] == ["2022-02-23"]
    assert f2qs["partition"] == ["2022-02-23"]
    assert f3qs["partition"] == ["2022-02-23"]
    assert len(f1qs["commit_id"]) == 1
    commit_id = f1qs["commit_id"][0]
    assert f2qs["commit_id"] == [commit_id]
    assert f3qs["commit_id"] == [commit_id]

    assert outputs.a.a == 10
    assert outputs.a.b == "s"
    assert outputs.c == 100

    commit2 = dataset_read_commit_service.get_commit(
        DatasetReadSpecifications(
            name="dataset2",
            namespace="namespace1",
            partition="2022-02-23",
            path_in_dataset="",
            snapshot=None,
            commit_id=commit_id,
        )
    )
    assert commit2 is not None
    assert commit2.id == commit_id
    assert commit2.dataset_name == "dataset2"
    assert commit2.dataset_namespace == "namespace1"
    assert commit2.partition == "2022-02-23"
    assert commit2.parent_commits == (commit1.as_parent_dataset_commit(),)
    assert re.match("^mock://mockloc/dataset2/namespace1/2022-02-23/[^/]+$", commit2.uri)

    # case 3, use the two dataset published above as input, publish another partition of second
    # dataset
    # output commit should have two parents, the commits of the two datasets.
    input_uri_1 = (
        "ampds://datASet1/path/to/folder/output_1?partition=2022-02-23&namespace=namespace1"
    )
    expected_resolved_pattern_1 = (
        "^mock://mockloc/datASet1/namespace1/2022-02-23/[^/]+/path/to/folder/output_1$"
    )
    input_uri_2 = "ampds://dataset2/output_2?partition=2022-02-23&namespace=namespace1"
    expected_resolved_pattern_2 = "^mock://mockloc/dataset2/namespace1/2022-02-23/[^/]+/output_2$"
    output_base_uri = "ampds://dataset2?partition=2022-02-24&namespace=namespace1"
    expected_resolved_output_base_uri_pattern = (
        "^mock://mockloc/dataset2/namespace1/2022-02-24/[^/]+$"
    )

    pl = get_verification_pipeline_1(
        expected_input_uri_1_pattern=expected_resolved_pattern_1,
        expected_input_uri_2_pattern=expected_resolved_pattern_2,
        expected_output_base_uri_pattern=expected_resolved_output_base_uri_pattern,
    )
    pl = publish_outputs_as_dataset(pl)
    inputs = {
        "output_base_uri": output_base_uri,
        "y": 3.4,
        "allow_overwrite": False,
        "input_uris.i1": input_uri_1,
        "input_uris.i2": input_uri_2,
        "x.a": 1.0,
        "x.b": "s",
    }
    runner = pipeline_runner_factory(pl)
    outputs = runner(inputs)

    f1 = urlparse(outputs.output_uris.o1)
    f2 = urlparse(outputs.output_uris.o2)
    f3 = urlparse(outputs.output_uris.o3)
    f1qs = parse_qs(f1.query)
    f2qs = parse_qs(f2.query)
    f3qs = parse_qs(f3.query)

    assert f1.path == "/output_1"
    assert f2.path == "/output_2"
    assert f3.path == "/output_3"
    assert f1.scheme == "ampds"
    assert f2.scheme == "ampds"
    assert f3.scheme == "ampds"
    assert f1.netloc == "dataset2"
    assert f2.netloc == "dataset2"
    assert f3.netloc == "dataset2"
    assert f1qs["namespace"] == ["namespace1"]
    assert f2qs["namespace"] == ["namespace1"]
    assert f3qs["namespace"] == ["namespace1"]
    assert f1qs["partition"] == ["2022-02-24"]
    assert f2qs["partition"] == ["2022-02-24"]
    assert f3qs["partition"] == ["2022-02-24"]
    assert len(f1qs["commit_id"]) == 1
    commit_id = f1qs["commit_id"][0]
    assert f2qs["commit_id"] == [commit_id]
    assert f3qs["commit_id"] == [commit_id]

    assert outputs.a.a == 10
    assert outputs.a.b == "s"
    assert outputs.c == 100

    commit3 = dataset_read_commit_service.get_commit(
        DatasetReadSpecifications(
            name="dataset2",
            namespace="namespace1",
            partition="2022-02-24",
            path_in_dataset="",
            snapshot=None,
            commit_id=commit_id,
        )
    )
    assert commit3 is not None
    assert commit3.id == commit_id
    assert commit3.dataset_name == "dataset2"
    assert commit3.dataset_namespace == "namespace1"
    assert commit3.partition == "2022-02-24"
    assert commit3.parent_commits is not None
    assert len(commit3.parent_commits) == 2
    assert len(set(commit3.parent_commits)) == 2
    assert set(commit3.parent_commits) == set(
        (
            commit1.as_parent_dataset_commit(),
            commit2.as_parent_dataset_commit(),
        )
    )
    assert re.match("^mock://mockloc/dataset2/namespace1/2022-02-24/[^/]+$", commit3.uri)

    # case 4, repeat case 3, trying to publish to the same dataset and partition.
    # should fail, because allow_overwrite is False
    with pytest.raises(ValueError):
        runner(inputs)

    # case 5, repeat case 4, setting allow_overwrite to True
    # should succeed, and create a new commit overwriting commit3
    inputs["allow_overwrite"] = True
    outputs = runner(inputs)

    f1 = urlparse(outputs.output_uris.o1)
    f2 = urlparse(outputs.output_uris.o2)
    f3 = urlparse(outputs.output_uris.o3)
    f1qs = parse_qs(f1.query)
    f2qs = parse_qs(f2.query)
    f3qs = parse_qs(f3.query)

    assert f1.path == "/output_1"
    assert f2.path == "/output_2"
    assert f3.path == "/output_3"
    assert f1.scheme == "ampds"
    assert f2.scheme == "ampds"
    assert f3.scheme == "ampds"
    assert f1.netloc == "dataset2"
    assert f2.netloc == "dataset2"
    assert f3.netloc == "dataset2"
    assert f1qs["namespace"] == ["namespace1"]
    assert f2qs["namespace"] == ["namespace1"]
    assert f3qs["namespace"] == ["namespace1"]
    assert f1qs["partition"] == ["2022-02-24"]
    assert f2qs["partition"] == ["2022-02-24"]
    assert f3qs["partition"] == ["2022-02-24"]
    assert len(f1qs["commit_id"]) == 1
    commit_id = f1qs["commit_id"][0]
    assert f2qs["commit_id"] == [commit_id]
    assert f3qs["commit_id"] == [commit_id]

    assert outputs.a.a == 10
    assert outputs.a.b == "s"
    assert outputs.c == 100

    commit5 = dataset_read_commit_service.get_commit(
        DatasetReadSpecifications(
            name="dataset2",
            namespace="namespace1",
            partition="2022-02-24",
            path_in_dataset="",
            snapshot=None,
            commit_id=commit_id,
        )
    )
    assert commit5 is not None
    assert commit5.id != commit3.id
    assert commit5.id == commit_id
    assert commit5.dataset_name == commit3.dataset_name
    assert commit5.dataset_namespace == commit3.dataset_namespace
    assert commit5.partition == commit3.partition
    assert commit5.parent_commits is not None
    assert set(commit5.parent_commits) == set(commit3.parent_commits)
    assert commit5.uri != commit3.uri
    assert re.match("^mock://mockloc/dataset2/namespace1/2022-02-24/[^/]+$", commit5.uri)

    # case 6, input 1 is a dataset, input 2 and output are not
    input_uri_1 = (
        "ampds://datASet1/path/to/folder/output_1?partition=2022-02-23&namespace=namespace1"
    )
    expected_resolved_pattern_1 = (
        "^mock://mockloc/datASet1/namespace1/2022-02-23/[^/]+/path/to/folder/output_1$"
    )
    input_uri_2 = "file:///path1/to/file2"
    expected_resolved_pattern_2 = "^file:///path1/to/file2$"
    output_base_uri = "file:///path_to_output/under_here"
    expected_resolved_output_base_uri_pattern = "^file:///path_to_output/under_here$"

    pl = get_verification_pipeline_1(
        expected_input_uri_1_pattern=expected_resolved_pattern_1,
        expected_input_uri_2_pattern=expected_resolved_pattern_2,
        expected_output_base_uri_pattern=expected_resolved_output_base_uri_pattern,
    )
    pl = publish_outputs_as_dataset(pl)
    inputs = {
        "output_base_uri": output_base_uri,
        "y": 3.4,
        "allow_overwrite": False,
        "input_uris.i1": input_uri_1,
        "input_uris.i2": input_uri_2,
        "x.a": 1.0,
        "x.b": "s",
    }
    runner = pipeline_runner_factory(pl)
    outputs = runner(inputs)

    assert outputs.output_uris.o1 == extend_uri_path(output_base_uri, "output_1")
    assert outputs.output_uris.o2 == extend_uri_path(output_base_uri, "output_2")
    assert outputs.output_uris.o3 == extend_uri_path(output_base_uri, "output_3")
    assert outputs.a.a == 10
    assert outputs.a.b == "s"
    assert outputs.c == 100


def test_service_exists(app: OnemlApp) -> None:
    app.get_service(OnemlHabitatsPipelineOperationsServices.PUBLISH_OUTPUTS_AS_DATASET)
