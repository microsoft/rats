from rats.processors._legacy_subpackages.pipeline_operations import (
    CollectionToDict,
    DictToCollection,
    ExposeGivenOutputs,
)
from rats.processors._legacy_subpackages.ux import PipelineRunnerFactory, UPipelineBuilder


def test_collection_to_dict_uniform_types(collection_to_dict: CollectionToDict) -> None:
    to_dict = collection_to_dict(entries=("v1", "v2"), element_type=int)
    assert set(to_dict.inputs) == {"col"}
    assert set(to_dict.inputs.col) == {"v1", "v2"}
    assert set(to_dict.outputs) == {"dct"}
    assert len(to_dict._dag.nodes) == 1
    node = next(iter(to_dict._dag.nodes.values()))
    assert node.outputs["dct"].annotation.__annotations__ == dict(v1=int, v2=int)


def test_collection_to_dict_different_types(collection_to_dict: CollectionToDict) -> None:
    to_dict = collection_to_dict(entries_to_types=dict(v1=int, v2=str))
    assert set(to_dict.inputs) == {"col"}
    assert set(to_dict.inputs.col) == {"v1", "v2"}
    assert set(to_dict.outputs) == {"dct"}
    assert len(to_dict._dag.nodes) == 1
    node = next(iter(to_dict._dag.nodes.values()))
    assert node.outputs["dct"].annotation.__annotations__ == dict(v1=int, v2=str)


def test_collection_to_dict_wiring(
    expose_given_outputs: ExposeGivenOutputs,
    collection_to_dict: CollectionToDict,
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    to_dict = collection_to_dict(entries_to_types=dict(v1=int, v2=str))
    inp = expose_given_outputs(outputs={"q.v1": 10, "q.v2": "a"})

    p = UPipelineBuilder.combine(
        [inp, to_dict],
        name="p",
        dependencies=(inp.outputs.q >> to_dict.inputs.col,),
    )
    assert set(p.inputs) == set()
    assert set(p.outputs) == {"dct"}

    r = pipeline_runner_factory(p)
    o = r()
    assert o.dct == dict(v1=10, v2="a")


def test_dict_to_collection_uniform_types(dict_to_collection: DictToCollection) -> None:
    from_dict = dict_to_collection(entries=("v1", "v2"), element_type=int)
    assert set(from_dict.inputs) == {"dct"}
    assert set(from_dict.outputs) == {"col"}
    assert set(from_dict.outputs.col) == {"v1", "v2"}
    assert len(from_dict.outputs.col.v1) == 1
    assert next(iter(from_dict.outputs.col.v1)).param.annotation == int
    assert len(from_dict.outputs.col.v2) == 1
    assert next(iter(from_dict.outputs.col.v2)).param.annotation == int


def test_dict_to_collection_different_types(dict_to_collection: DictToCollection) -> None:
    from_dict = dict_to_collection(entries_to_types=dict(v1=int, v2=str))
    assert set(from_dict.inputs) == {"dct"}
    assert set(from_dict.outputs) == {"col"}
    assert set(from_dict.outputs.col) == {"v1", "v2"}
    assert len(from_dict.outputs.col.v1) == 1
    assert next(iter(from_dict.outputs.col.v1)).param.annotation == int
    assert len(from_dict.outputs.col.v2) == 1
    assert next(iter(from_dict.outputs.col.v2)).param.annotation == str


def test_dict_to_collection_wiring(
    expose_given_outputs: ExposeGivenOutputs,
    dict_to_collection: DictToCollection,
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    from_dict = dict_to_collection(entries_to_types=dict(v1=int, v2=str))
    inp = expose_given_outputs(outputs={"q": {"v1": 10, "v2": "a"}})
    p = UPipelineBuilder.combine(
        [inp, from_dict],
        name="p",
        dependencies=(inp.outputs.q >> from_dict.inputs.dct,),
    )
    assert set(p.inputs) == set()
    assert set(p.outputs) == {"col"}
    assert set(p.outputs.col) == {"v1", "v2"}

    r = pipeline_runner_factory(p)
    o = r()
    assert o.col.v1 == 10
    assert o.col.v2 == "a"
