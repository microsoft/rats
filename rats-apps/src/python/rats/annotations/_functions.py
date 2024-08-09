from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from functools import cache
from typing import Any, Generic, ParamSpec, TypeVar
from typing import NamedTuple as tNamedTuple

from typing_extensions import NamedTuple

T_GroupType = TypeVar("T_GroupType", bound=NamedTuple)


class GroupAnnotations(NamedTuple, Generic[T_GroupType]):
    """The list of T_GroupType objects identified by a given name in a namespace."""

    name: str
    """The name of the annotation, typically the name of the function in a class"""
    namespace: str
    """All the groups in a namespace are expected to be of the same T_GroupType."""
    groups: tuple[T_GroupType, ...]


class AnnotationsContainer(tNamedTuple):
    """
    Holds metadata about the annotated functions or class methods.

    Loosely inspired by: https://peps.python.org/pep-3107/.
    """

    annotations: tuple[GroupAnnotations[Any], ...]

    @staticmethod
    def empty() -> AnnotationsContainer:
        return AnnotationsContainer(annotations=())

    def with_group(
        self,
        namespace: str,
        group_id: NamedTuple,
    ) -> AnnotationsContainer:
        return AnnotationsContainer(
            annotations=tuple(
                [
                    annotation_group
                    for x in self.with_namespace(namespace)
                    for annotation_group in x
                    if group_id in annotation_group.groups
                ]
            ),
        )

    def with_namespace(
        self,
        namespace: str,
    ) -> AnnotationsContainer:
        return AnnotationsContainer(
            annotations=tuple([x for x in self.annotations if x.namespace == namespace]),
        )


class AnnotationsBuilder:
    _group_ids: dict[str, set[Any]]

    def __init__(self) -> None:
        self._group_ids = defaultdict(set)

    def add(self, namespace: str, group_id: NamedTuple | tNamedTuple) -> None:
        self._group_ids[namespace].add(group_id)

    def make(self, name: str) -> AnnotationsContainer:
        return AnnotationsContainer(
            annotations=tuple(
                [
                    GroupAnnotations[Any](name=name, namespace=namespace, groups=tuple(groups))
                    for namespace, groups in self._group_ids.items()
                ]
            ),
        )


DecoratorType = TypeVar("DecoratorType", bound=Callable[..., Any])


def annotation(
    namespace: str,
    group_id: NamedTuple | tNamedTuple,
) -> Callable[[DecoratorType], DecoratorType]:
    """
    Decorator to add an annotation to a function.

    Typically used to create domain-specific annotation functions for things like DI Containers.
    For examples, see the rats.apps annotations, like service() and group().
    """

    def decorator(fn: DecoratorType) -> DecoratorType:
        if not hasattr(fn, "__rats_annotations__"):
            fn.__rats_annotations__ = AnnotationsBuilder()  # type: ignore[reportFunctionMemberAccess]

        fn.__rats_annotations__.add(namespace, group_id)  # type: ignore[reportFunctionMemberAccess]

        return fn

    return decorator


@cache
def get_class_annotations(cls: type) -> AnnotationsContainer:
    """
    Get all annotations for a class.

    Traverses the class methods looking for any annotated with "__rats_annotations__" and returns
    an instance of AnnotationsContainer. This function tries to cache the results to avoid any
    expensive parsing of the class methods.
    """
    tates: list[GroupAnnotations[Any]] = []

    for method_name in dir(cls):
        method = getattr(cls, method_name)
        if not hasattr(method, "__rats_annotations__"):
            continue

        builder: AnnotationsBuilder = method.__rats_annotations__
        tates.extend(builder.make(method_name).annotations)

    return AnnotationsContainer(annotations=tuple(tates))


P = ParamSpec("P")


def get_annotations(fn: Callable[..., Any]) -> AnnotationsContainer:
    """
    Get all annotations for a function or class method.

    Builds an instance of AnnotationsContainer from the annotations found in the object's
    "__rats_annotations__" attribute.
    """
    builder: AnnotationsBuilder = getattr(
        fn,
        "__rats_annotations__",
        AnnotationsBuilder(),
    )

    return builder.make(fn.__name__)
