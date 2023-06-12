"""
The oneml.services package provides libraries needed to register and initialize services (objects in the data-structures vs objects dichotomy of Clean Code) used
by the oneml applications. Services are initialized by OneMl Factories, cached by OneMl Containers,
and configured by OneMl Settings. Each of these layers contain a Registry object that allows us to
register/retrieve items by an Id Data Structure. Services are identified by a ServiceId, and
settings are identified by a SettingId.

While a service represents client objects, settings are generic data structures that are bound to
the NamedTuple type. Settings should be immutable data structures containing only primitive types.

In order to support services that are aware of the current execution context, there is a special
settings registry that returns contextual setting values. A Context is a setting value tied to the
state the pipeline is currently in. For example, we can have the service container return a
different io client depending on the currently running pipeline app, session, or node. You can
think of a context as a SettingId that is bound to a mutable state. Alternatively, you can think of
contexts as a setting that is opened and closed like a file handle.

```python
----- option 1 -----
class AppContext(NamedTuple):
    app_id: str


class PipelineSessionContext(NamedTuple):
    app_id: str
    session_id: str


class PipelineNodeContext(NamedTuple):
    app_id: str
    session_id: str
    node_id: str

----- option 2 -----
class AppContext(NamedTuple):
    app_id: str


class PipelineSessionContext(NamedTuple):
    session_id: str


class PipelineNodeContext(NamedTuple):
    node_id: str



class NodePublisher:

    _node_provider: PipelineNodeContextProvider

    def publish(self, port, data):
        node = self._node_provider.get_context()
        self._publisher.publish((node, port), data)


class NodePublisher:

    _node: PipelineNodeContext
    _publisher: DataPublisher

    def publish(self, port, data):
        self._publisher.publish((self._node, port), data)


@provider(ServiceId("node-publisher"))
@input_service(ServiceId("node-context-provider"))
def provider(node_provider) -> NodePublisher:
    return NodePublisher(
        node_provider=node_provider,
        publisher=app.get_service(ServiceId("data-publisher")),
    )


@provider(ServiceId("data-publisher"))
def provider(publisher_map) -> DataPublisher:
    return DataPublisher(
        # publisher_map=self._app.get_setting(SettingsId("publisher-map")),
        publisher_map=publisher_map,
    )



with context_client.set_context(SettingId[AppContext]("app"), AppContext(str(uuid.uuid4()))):
    active_app = context_client.get_context(SettingId[AppContext]("app"))
    print(active_app.app_id)  # This will be the uuid value from above

# When a context is "closed", retrieving it will raise an exception.
context_client.get_context(SettingId[AppContext]("app"))


# Process 1
app:
    app_id: {uuid}
    session:
        session_id: {uuid}
        node:
            node_id: A
# Process 2
app:
    app_id: {uuid}
    session:
        session_id: {uuid}
        node:
            node_id: B

app/{uuid}/session/{uuid}/process/{process-id}/node/{node-id}

app:
    app_id: {uuid}
    session:
        session_id: {uuid}
        process:
            process_id: 1
            node:
                node_id: B


Settings:
    gpus: 0
    cpus: 2
    debug_level: 0
    nodes:
        A:
            gpus: 1
        B:
            gpus: 3
            debug_level: 6
        C:
            cpus: 4

From Discussion:
- settings are made hierarchical by the context
- setting values are immutable
- the settings dictionary is append-only
- asking for a setting id, returns the value for the current context by traversing the dictionary
  from current context id, to the root context id
```

Services are registered by providing a callable, which is invoked when the service is requested.
Settings are set once and never modified, so they are registered by providing a value.
"""
from ._containers import (
    ContextualServiceContainer,
    FilteredServiceContainer,
    IDefineServices,
    IManageServices,
    IProvideServices,
    ServiceContainer,
    ServiceFactory,
    ServiceProvider,
    TypedServiceContainer,
)
from ._decorators import (
    group,
    groups,
    provider,
    providers,
    scoped_service_ids,
)
from ._service_id import ServiceId, ServiceType
from ._settings import (SettingProvider)

__all__ = [
    # _containers
    "ContextualServiceContainer",
    "FilteredServiceContainer",
    "IDefineServices",
    "IManageServices",
    "IProvideServices",
    "ServiceContainer",
    "ServiceFactory",
    "ServiceProvider",
    "TypedServiceContainer",
    # _decorators
    "group",
    "groups",
    "provider",
    "providers",
    "scoped_service_ids",
    # _entity
    "ServiceId",
    "ServiceType",
    # _settings
    "SettingProvider",
]
