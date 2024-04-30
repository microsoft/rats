from collections import defaultdict
from typing import Any, Generic

from typing_extensions import NamedTuple

from ._groups import GroupAnnotations, T_GroupType


class FunctionAnnotations(NamedTuple, Generic[T_GroupType]):
    """
    Holds metadata about the annotated service provider.

    Loosely inspired by: https://peps.python.org/pep-3107/.
    """

    providers: tuple[GroupAnnotations[T_GroupType], ...]

    def group_in_namespace(
        self,
        namespace: str,
        group_id: T_GroupType,
    ) -> tuple[GroupAnnotations[T_GroupType], ...]:
        return tuple([x for x in self.with_namespace(namespace) if group_id in x.groups])

    def with_namespace(
        self,
        namespace: str,
    ) -> tuple[GroupAnnotations[T_GroupType], ...]:
        return tuple([x for x in self.providers if x.namespace == namespace])


class FunctionAnnotationsBuilder(Generic[T_GroupType]):
    _group_ids: dict[str, list[T_GroupType]]

    def __init__(self) -> None:
        self._group_ids = defaultdict(list)

    def add(self, namespace: str, group_id: T_GroupType) -> None:
        self._group_ids[namespace].append(group_id)

    def make(self, name: str) -> tuple[GroupAnnotations[Any], ...]:
        return tuple(
            [
                GroupAnnotations[Any](name=name, namespace=namespace, groups=tuple(groups))
                for namespace, groups in self._group_ids.items()
            ]
        )
