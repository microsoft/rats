# type: ignore
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from functools import cache
from typing import Any, NamedTuple, ParamSpec, T

from rats.annotations._groups import GroupAnnotations, T_GroupType


class AnnotationsContainer(NamedTuple):
    """
    Holds metadata about the annotated service provider.

    Loosely inspired by: https://peps.python.org/pep-3107/.
    """

    annotations: tuple[GroupAnnotations[...], ...]

    @staticmethod
    def empty() -> AnnotationsContainer:
        return AnnotationsContainer(annotations=())

    def with_group(
        self,
        namespace: str,
        group_id: T_GroupType,
    ) -> AnnotationsContainer:
        return AnnotationsContainer(
            annotations=tuple([x for x in self.with_namespace(namespace) if group_id in x.groups]),
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

    def add(self, namespace: str, group_id: NamedTuple) -> None:
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


AnnotationDecorator = Callable[[T], T]


def annotation(namespace: str, group_id: NamedTuple) -> AnnotationDecorator:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if not hasattr(fn, "__rats_annotations__"):
            fn.__rats_annotations__ = AnnotationsBuilder()  # type: ignore[reportFunctionMemberAccess]

        fn.__rats_annotations__.add(namespace, group_id)  # type: ignore[reportFunctionMemberAccess]

        return fn

    return decorator


@cache
def get_class_annotations(cls: type) -> AnnotationsContainer:
    tates = []

    for method_name in dir(cls):
        method = getattr(cls, method_name)
        if not hasattr(method, "__rats_annotations__"):
            continue

        tates.extend(method.__rats_annotations__.make(method_name).annotations)

    return AnnotationsContainer(annotations=tuple(tates))


P = ParamSpec("P")


def get_annotations(fn: Callable[..., Any]) -> AnnotationsContainer:
    builder: AnnotationsBuilder = getattr(
        fn,
        "__rats_annotations__",
        AnnotationsBuilder(),
    )

    return builder.make(fn.__name__)
