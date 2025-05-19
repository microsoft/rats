"""
Allows marshaling of simple value objects across processes and machines.

The [rats.app_context.Collection][] and [rats.app_context.Context][] classes are the building
blocks for creating a collection of services that can be serialized to json and shared across
applications. In order to be easily serializable, all service values managed by this module must
be instances of [dataclasses.dataclass][], must be immutable, and must be made up of simple value
types.

!!! example
    If we have an example data structure, `MySimpleData`, we can store instances of it into a
    [rats.app_context.Context][] object by assigning them a service id. Every service id in a
    context maps to zero or more instances of our data structure. Zero or more context objects can
    be used to create [rats.app_context.Collection][] instances, which can be serialized with the
    [rats.app_context.dumps][] and [rats.app_context.loads][] functions.

    ```python
    from dataclasses import dataclass
    from rats import apps, app_context


    @dataclass(frozen=True)
    class MySimpleData:
        blob_path: tuple[str, str, str]
        offset: int


    data1 = MySimpleData(
        blob_path=("accountname", "containername", "/some/blob/path"),
        offset=3,
    )

    data2 = MySimpleData(
        blob_path=("accountname", "containername", "/another/blob/path"),
        offset=3,
    )

    service_id = apps.ServiceId[MySimpleData]("example-service")

    ctx = app_context.Context[MySimpleData].make(service_id, data1, data2)
    collection = app_context.Collection.make(ctx)

    # the encoded json string can be moved between machines through files, env variables, etc.
    json_encoded = app_context.dumps(collection)
    # on the remote process, we can rebuild the original collection object
    original_collection = app_context.loads(json_encoded)
    # we can retrieve the json-encoded contexts
    values = original_collection.values(service_id)
    # and we can decode the values back into the `MySimpleData` instances
    simple_data_instances = original_collection.decoded_values(MySimpleData, service_id)
    ```
"""

from ._collection import (
    EMPTY_COLLECTION,
    Collection,
    dumps,
    loads,
)
from ._container import GroupContainer, ServiceContainer
from ._context import Context, ContextValue, T_ContextType

__all__ = [
    "EMPTY_COLLECTION",
    "Collection",
    "Context",
    "ContextValue",
    "GroupContainer",
    "ServiceContainer",
    "T_ContextType",
    "dumps",
    "loads",
]
