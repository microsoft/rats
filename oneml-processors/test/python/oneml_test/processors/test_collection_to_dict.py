from oneml.processors.training import CollectionToDictBuilder
from oneml.processors.ux import (
    CombinedPipeline,
    FixedOutputProcessor,
    PipelineRunnerFactory,
    UPipeline,
    UTask,
)


def test_collection_to_dict_uniform_types() -> None:
    to_dict = CollectionToDictBuilder.build("c", entries=set(("v1", "v2")), element_type=int)
    assert set(to_dict.inputs) == set()
    assert set(to_dict.in_collections) == set(("c",))
    assert set(to_dict.in_collections.c) == set(("v1", "v2"))
    assert set(to_dict.outputs) == set(("c",))
    assert set(to_dict.out_collections) == set()
    assert len(to_dict._dag.nodes) == 1
    node = next(iter(to_dict._dag.nodes.values()))
    assert node.outputs["c"].annotation.__annotations__ == dict(v1=int, v2=int)


def test_collection_to_dict_different_types() -> None:
    to_dict = CollectionToDictBuilder.build("c", entries_to_types=dict(v1=int, v2=str))
    assert set(to_dict.inputs) == set()
    assert set(to_dict.in_collections) == set(("c",))
    assert set(to_dict.in_collections.c) == set(("v1", "v2"))
    assert set(to_dict.outputs) == set(("c",))
    assert set(to_dict.out_collections) == set()
    assert len(to_dict._dag.nodes) == 1
    node = next(iter(to_dict._dag.nodes.values()))
    assert node.outputs["c"].annotation.__annotations__ == dict(v1=int, v2=str)


def test_collection_to_dict_wiring(
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    to_dict = CollectionToDictBuilder.build("c", entries_to_types=dict(v1=int, v2=str))
    assert set(to_dict.inputs) == set()
    assert set(to_dict.in_collections) == set(("c",))
    assert set(to_dict.in_collections.c) == set(("v1", "v2"))
    assert set(to_dict.outputs) == set(("c",))
    assert set(to_dict.out_collections) == set()

    in1 = UTask(
        FixedOutputProcessor,
        name="in1",
        config=dict(data=10),
        return_annotation=dict(data=int),
    )
    in2 = UTask(
        FixedOutputProcessor,
        name="in2",
        config=dict(data="a"),
        return_annotation=dict(data=str),
    )
    p: UPipeline = CombinedPipeline(
        [in1, in2, to_dict],
        name="p",
        dependencies=(
            in1.outputs.data >> to_dict.in_collections.c.v1,
            in2.outputs.data >> to_dict.in_collections.c.v2,
        ),
    )
    assert set(p.inputs) == set()
    assert set(p.in_collections) == set()
    assert set(p.outputs) == set(("c",))
    assert set(p.out_collections) == set()

    r = pipeline_runner_factory(p)
    o = r()
    assert o.c == dict(v1=10, v2="a")
