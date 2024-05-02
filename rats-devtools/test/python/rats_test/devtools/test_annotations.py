from typing_extensions import NamedTuple

from rats.annotations import AnnotationsContainer, annotation, get_annotations


class SimpleTuple(NamedTuple):
    name: str


@annotation(namespace="test_namespace", group_id=SimpleTuple("group1"))
@annotation(namespace="test_namespace", group_id=SimpleTuple("group2"))
def test_function():
    pass


def test_group_annotations():
    group_annotations = get_annotations(test_function).annotations[0]

    assert group_annotations.name == "test_function"
    assert group_annotations.namespace == "test_namespace"
    assert set(group_annotations.groups) == {SimpleTuple("group1"), SimpleTuple("group2")}


@annotation(namespace="ns1", group_id=SimpleTuple("group1"))
def test_function1():
    pass


@annotation(namespace="ns2", group_id=SimpleTuple("group2"))
def test_function2():
    pass


def test_with_namespace():
    annotations_container = AnnotationsContainer(
        annotations=(
            get_annotations(test_function1).annotations[0],
            get_annotations(test_function2).annotations[0],
        )
    )
    filtered_annotations = annotations_container.with_namespace("ns1")

    assert len(filtered_annotations) == 1
    assert filtered_annotations.annotations[0].namespace == "ns1"
    assert filtered_annotations.annotations[0].groups == (SimpleTuple("group1"),)
    assert filtered_annotations.annotations[0].name == "test_function1"


@annotation(namespace="ns1", group_id=SimpleTuple("group1"))
def test_function3():
    pass


def test_group_in_namespace():
    annotations_container = AnnotationsContainer(
        annotations=(
            get_annotations(test_function1).annotations[0],
            get_annotations(test_function2).annotations[0],
            get_annotations(test_function3).annotations[0],
        )
    )
    filtered_annotations = annotations_container.with_group("ns1", SimpleTuple("group1"))

    assert len(filtered_annotations) == 1
    assert filtered_annotations.annotations[0].groups == (SimpleTuple("group1"),)


@annotation(namespace="ns1", group_id=SimpleTuple("group1"))
@annotation(namespace="ns1", group_id=SimpleTuple("group2"))
def test_function4():
    pass


def test_add_and_make():
    annotations = get_annotations(test_function4)

    assert len(annotations) == 1
    assert annotations.annotations[0].name == "test_function4"
    assert annotations.annotations[0].namespace == "ns1"
    assert set(annotations.annotations[0].groups) == {SimpleTuple("group2"), SimpleTuple("group1")}
