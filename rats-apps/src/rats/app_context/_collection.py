from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Generic, final

import dataclass_wizard

from rats import apps

from ._context import Context, ContextValue, T_ContextType

logger = logging.getLogger(__name__)


@final
@dataclass(frozen=True)
class Collection(Generic[T_ContextType]):
    """
    Collection of context objects linking service ids to serializable data structures.

    It is up to the user of this class to provide the correct mapping between services and the
    constructor for those services.
    """

    items: tuple[Context[T_ContextType], ...]

    @staticmethod
    def merge(*collections: Collection[T_ContextType]) -> Collection[T_ContextType]:
        return Collection[T_ContextType].make(
            *[ctx for collection in collections for ctx in collection.items]
        )

    @staticmethod
    def empty() -> Collection[T_ContextType]:
        """Useful when wanting to define a simple default value for a context collection."""
        return Collection(items=())

    @staticmethod
    def make(*items: Context[T_ContextType]) -> Collection[T_ContextType]:
        # just a handy shortcut to remove a nested tuple from the end-user code.
        return Collection(items=items)

    def service_ids(self) -> set[apps.ServiceId[T_ContextType]]:
        return {item.service_id for item in self.items}

    def decoded_values(
        self,
        cls: type[T_ContextType],
        service_id: apps.ServiceId[T_ContextType],
    ) -> tuple[T_ContextType, ...]:
        return tuple(dataclass_wizard.fromlist(cls, list(self.values(service_id))))

    def values(self, service_id: apps.ServiceId[T_ContextType]) -> tuple[ContextValue, ...]:
        results: list[ContextValue] = []
        for item in self.with_id(service_id).items:
            for value in item.values:
                results.append(value)

        return tuple(results)

    def add(self, *items: Context[T_ContextType]) -> Collection[T_ContextType]:
        """Creates a new Collection with the provided items added to the current ones."""
        return Collection[T_ContextType].make(
            *self.items,
            *items,
        )

    def with_id(self, *service_ids: apps.ServiceId[T_ContextType]) -> Collection[T_ContextType]:
        """Filter out context items not matching the provided service ids and return a new Collection."""
        return Collection[T_ContextType](
            items=tuple(item for item in self.items if item.service_id in service_ids),
        )


EMPTY_COLLECTION = Collection[Any].empty()
"""Empty collection constant usable as default method values."""


def loads(context: str) -> Collection[Any]:
    """
    Transforms a json string into a [rats.app_context.Collection][] instance.

    This function does not attempt to validate the mapping between services and their values.

    Args:
        context: json string containing an `items` key of `service_id`, `values` mappings.
    """
    data = json.loads(context)
    return Collection[Any](
        items=tuple(
            [
                Context(
                    service_id=apps.ServiceId(*x["serviceId"]),
                    values=tuple(x["values"]),
                )
                for x in data["items"]
            ]
        ),
    )


def dumps(collection: Collection[Any]) -> str:
    """
    Serializes a [rats.app_context.Collection][] instance to a json string.

    Args:
        collection: collection of serializable services wanting to be shared between machines.

    Returns: a string that can easily be shared between machines.

    """
    return json.dumps(dataclass_wizard.asdict(collection))  # type: ignore
