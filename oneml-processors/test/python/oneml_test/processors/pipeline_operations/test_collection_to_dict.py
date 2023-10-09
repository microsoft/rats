from oneml.processors.pipeline_operations import (
    CollectionToDict,
    DictToCollection,
    ExposeGivenOutputs,
)
from oneml.processors.ux import PipelineRunnerFactory, UPipelineBuilder


def test_collection_to_dict_uniform_types(collection_to_dict: CollectionToDict) -> None:
    to_dict = collection_to_dict(entries=("v1", "v2"), element_type=int)
    assert set(to_dict.inputs) == set()
    assert set(to_dict.in_collections) == {
        "col",
    }
    assert set(to_dict.in_collections.col) == {"v1", "v2"}
    assert set(to_dict.outputs) == {
        "dct",
    }
    assert set(to_dict.out_collections) == set()
    assert len(to_dict._dag.nodes) == 1
    node = list(to_dict._dag.nodes.values())[0]
    node.outputs["dct"].annotation.__annotations__ == dict(v1=int, v2=int)


def test_collection_to_dict_different_types(collection_to_dict: CollectionToDict) -> None:
    to_dict = collection_to_dict(entries_to_types=dict(v1=int, v2=str))
    assert set(to_dict.inputs) == set()
    assert set(to_dict.in_collections) == {
        "col",
    }
    assert set(to_dict.in_collections.col) == {"v1", "v2"}
    assert set(to_dict.outputs) == {
        "dct",
    }
    assert set(to_dict.out_collections) == set()
    assert len(to_dict._dag.nodes) == 1
    node = list(to_dict._dag.nodes.values())[0]
    node.outputs["dct"].annotation.__annotations__ == dict(v1=int, v2=str)


def test_collection_to_dict_wiring(
    expose_given_outputs: ExposeGivenOutputs,
    collection_to_dict: CollectionToDict,
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    to_dict = collection_to_dict(entries_to_types=dict(v1=int, v2=str))
    inp = expose_given_outputs(out_collections=dict(q=dict(v1=10, v2="a")))

    p = UPipelineBuilder.combine(
        [inp, to_dict],
        name="p",
        dependencies=(inp.out_collections.q >> to_dict.in_collections.col,),
    )
    assert set(p.inputs) == set()
    assert set(p.in_collections) == set()
    assert set(p.outputs) == {
        "dct",
    }
    assert set(p.out_collections) == set()

    r = pipeline_runner_factory(p)
    o = r()
    assert o.dct == dict(v1=10, v2="a")


def test_dict_to_collection_uniform_types(dict_to_collection: DictToCollection) -> None:
    from_dict = dict_to_collection(entries=("v1", "v2"), element_type=int)
    assert set(from_dict.inputs) == {"dct"}
    assert set(from_dict.in_collections) == set()
    assert set(from_dict.outputs) == set()
    assert set(from_dict.out_collections) == {"col"}
    assert set(from_dict.out_collections.col) == {"v1", "v2"}
    assert len(from_dict.out_collections.col.v1) == 1
    assert list(from_dict.out_collections.col.v1)[0].param.annotation == int
    assert len(from_dict.out_collections.col.v2) == 1
    assert list(from_dict.out_collections.col.v2)[0].param.annotation == int


def test_dict_to_collection_different_types(dict_to_collection: DictToCollection) -> None:
    from_dict = dict_to_collection(entries_to_types=dict(v1=int, v2=str))
    assert set(from_dict.inputs) == {"dct"}
    assert set(from_dict.in_collections) == set()
    assert set(from_dict.outputs) == set()
    assert set(from_dict.out_collections) == {"col"}
    assert set(from_dict.out_collections.col) == {"v1", "v2"}
    assert len(from_dict.out_collections.col.v1) == 1
    assert list(from_dict.out_collections.col.v1)[0].param.annotation == int
    assert len(from_dict.out_collections.col.v2) == 1
    assert list(from_dict.out_collections.col.v2)[0].param.annotation == str


def test_dict_to_collection_wiring(
    expose_given_outputs: ExposeGivenOutputs,
    dict_to_collection: DictToCollection,
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    from_dict = dict_to_collection(entries_to_types=dict(v1=int, v2=str))
    inp = expose_given_outputs(outputs=dict(q=dict(v1=10, v2="a")))
    p = UPipelineBuilder.combine(
        [inp, from_dict],
        name="p",
        dependencies=(inp.outputs.q >> from_dict.inputs.dct,),
    )
    assert set(p.inputs) == set()
    assert set(p.in_collections) == set()
    assert set(p.outputs) == set()
    assert set(p.out_collections) == {"col"}
    assert set(p.out_collections.col) == {"v1", "v2"}

    r = pipeline_runner_factory(p)
    o = r()
    assert o.col.v1 == 10
    assert o.col.v2 == "a"
