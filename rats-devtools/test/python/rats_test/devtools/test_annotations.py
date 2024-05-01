from typing import NamedTuple

from rats.annotations import AnnotationsContainer, AnnotationsBuilder, GroupAnnotations


class SimpleTuple(NamedTuple):
    name: str


def test_group_annotations():
    group_annotations = GroupAnnotations(
        name="test_function",
        namespace="test_namespace",
        groups=(SimpleTuple("group1"), SimpleTuple("group2")),
    )

    assert group_annotations.name == "test_function"
    assert group_annotations.namespace == "test_namespace"
    assert group_annotations.groups == (SimpleTuple("group1"), SimpleTuple("group2"))


def test_with_namespace():
    group_annotations1 = GroupAnnotations(
        name="test_function1", namespace="ns1", groups=(SimpleTuple("group1"),)
    )
    group_annotations2 = GroupAnnotations(
        name="test_function2", namespace="ns2", groups=(SimpleTuple("group2"),)
    )
    annotations_container = AnnotationsContainer(annotations=(group_annotations1, group_annotations2))
    filtered_annotations = annotations_container.with_namespace("ns1").annotations

    assert len(filtered_annotations) == 1
    assert filtered_annotations[0].namespace == "ns1"
    assert filtered_annotations[0].groups == (SimpleTuple("group1"),)
    assert filtered_annotations[0].name == "test_function1"


def test_group_in_namespace():
    group_annotations1 = GroupAnnotations(
        name="test_function1",
        namespace="ns1",
        groups=(SimpleTuple("group1"),),
    )
    group_annotations2 = GroupAnnotations(
        name="test_function2",
        namespace="ns1",
        groups=(SimpleTuple("group2"),),
    )
    group_annotations3 = GroupAnnotations(
        name="test_function3",
        namespace="ns2",
        groups=(SimpleTuple("group2"),),
    )
    annotations_container = AnnotationsContainer(
        annotations=(group_annotations1, group_annotations2, group_annotations3)
    )
    filtered_annotations = annotations_container.with_group("ns1", SimpleTuple("group1")).annotations

    assert len(filtered_annotations) == 1
    assert filtered_annotations[0].groups == (SimpleTuple("group1"),)


def test_add_and_make():
    builder = FunctionAnnotationsBuilder[SimpleTuple]()
    builder.add("ns1", SimpleTuple("group1"))
    builder.add("ns1", SimpleTuple("group2"))
    annotations = builder.make("test_function")

    assert len(annotations) == 1
    assert annotations[0].name == "test_function"
    assert annotations[0].namespace == "ns1"
    assert annotations[0].groups == (SimpleTuple("group1"), SimpleTuple("group2"))
