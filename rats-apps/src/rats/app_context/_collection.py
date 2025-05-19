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
    """Access to the raw [rats.app_context.Context][] instances in the collection."""

    @staticmethod
    def merge(*collections: Collection[T_ContextType]) -> Collection[T_ContextType]:
        """
        Merge multiple collections into a new, combined instance.

        Args:
            *collections: zero or more collections to merge into one.
        """
        return Collection[T_ContextType].make(
            *[ctx for collection in collections for ctx in collection.items]
        )

    @staticmethod
    def empty() -> Collection[T_ContextType]:
        """A shortcut to retrieving an empty collection."""
        return Collection(items=())

    @staticmethod
    def make(*items: Context[T_ContextType]) -> Collection[T_ContextType]:
        """
        Convenience function to create a collection from a list of contexts.

        Args:
            *items: zero or more context objects to turn into a collection.
        """
        return Collection(items=items)

    def service_ids(self) -> set[apps.ServiceId[T_ContextType]]:
        """Get the list of service items found in the collection, across all context instances."""
        return {item.service_id for item in self.items}

    def decoded_values(
        self,
        cls: type[T_ContextType],
        service_id: apps.ServiceId[T_ContextType],
    ) -> tuple[T_ContextType, ...]:
        """
        Given a reference to a dataclass type, retrieves and builds instances matching a service id.

        !!! info
            The dataclass used in the two communicating processes does not need to be the same, but
            we expect the constructor arguments to be compatible.

        Args:
            cls: the type all selected context objects will be cast into before returning.
            service_id: the selector for the expected context objects.
        """
        return tuple(dataclass_wizard.fromlist(cls, list(self.values(service_id))))

    def values(self, service_id: apps.ServiceId[T_ContextType]) -> tuple[ContextValue, ...]:
        """
        Retrieves the raw data structures matching a service id.

        The values returned here have been encoded into simple dictionaries and are ready to be
        serialized and transferred across machines. See the
        [rats.app_context.Collection.decoded_values][] method to retrieve context values that have
        been turned back into the desired dataclass objects.

        Args:
            service_id: the selector for the expected context objects.
        """
        results: list[ContextValue] = []
        for item in self.with_id(service_id).items:
            for value in item.values:
                results.append(value)

        return tuple(results)

    def add(self, *items: Context[T_ContextType]) -> Collection[T_ContextType]:
        """
        Creates a new Collection with the provided items added to the current ones.

        Args:
            *items: the context items to be added in the new collection.
        """
        return Collection[T_ContextType].make(
            *self.items,
            *items,
        )

    def with_id(self, *service_ids: apps.ServiceId[T_ContextType]) -> Collection[T_ContextType]:
        """
        Filter out context items not matching the provided service ids and return a new Collection.

        Args:
            *service_ids: the selector for the returned context collection.
        """
        return Collection[T_ContextType](
            items=tuple(item for item in self.items if item.service_id in service_ids),
        )


# disable key transformation for our collection class
dataclass_wizard.DumpMeta(key_transform="NONE").bind_to(Collection)  # type: ignore[reportUnknownMemberType]
dataclass_wizard.LoadMeta(key_transform="NONE").bind_to(Collection)  # type: ignore[reportUnknownMemberType]
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
                    service_id=apps.ServiceId(*x["service_id"]),
                    values=tuple(x["values"]),
                )
                for x in data.get("items", [])
            ]
        ),
    )


def dumps(collection: Collection[Any]) -> str:
    """
    Serializes a [rats.app_context.Collection][] instance to a json string.

    Args:
        collection: collection of serializable services wanting to be shared between machines.
    """
    return json.dumps(dataclass_wizard.asdict(collection), indent=4)  # type: ignore
