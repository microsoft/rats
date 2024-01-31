# Future Documentation

## per component docs
- you can create a `docs` folder in any component
- python can be embedded into the documents
- the python runs in a new venv that has the current component as a dependency
- this ensures the example documentation is written with the perspective of package users
- this means we cannot document internal APIs, by design
- internal APIs need to be documented in internal documentation
- this is an attribute assigned to the document, by design
- each document has to belong to a single python package

## .drafts
All sites have a `.drafts` folder that does not get auto indexed and incorporated into the default
site navigation. The expectation is that a file is owned by a single individual and all
collaboration related to the contents of that file by other individuals is done via pull requests.

- I own a `lolo.md` file.
- I can make changes to the document.
- I can depend on the contents of the document.
- Others can submit requests to change the document.
- Others can submit requests to depend on the conntents of the document.
- Permissions to change the document are not related to permissions to depend on a draft entity.
- This draft is a draft entity itself.
- I only need permission to move the contents of this document, out of this document.
- Ownership of a draft document can be assigned to a group identity.
- TODO: Something about transparency here and transitioning and sharing ownership.

"""
- di container and service ids always belong to an app layer
- initializing objects is always an app-responsibility
- service ids are the edges between objects, so they belong with initialization logic
- watch out using service ids in libraries, it implies this is an app-specific library
"""

"""
Thoughts on APIs like the below:

```python
from typing import Protocol
from oneml.pipelines.dag import PipelineNode

class OnemlIoPlugin(Protocol):
    def on_node_completion(self, node: PipelineNode) -> None:
        """"""
```

It's often requested that we add arguments like `node` because we don't want to use the context
client everywhere. But this pattern makes us decide on the appropriate arguments to forward to
io plugins. The plugin system is supposed to decouple us from the implementation details of
plugins, but this pattern above decides what plugins should need before plugins are written.

My gut feeling is that we tend to like the above pattern because it reads well. Intuitively, an
event that fires when a node completes should forward the node datastructure. But this is a trap! We
need to focus on the target audience and design the API for them. We are providing an API for
IO focused plugins, and we are creating a new lifecycle event for when nodes complete, because
we think that will be useful to IO Plugin Authors. We do not want to depend on the
implementation details of IO Plugins, so we should not be able to tell what they need. An IO
Plugin that clears local tmp files after each node, does not need to import and depend on
`PipelineNode`.

IO Plugins that require information, can depend on that information's owner to provide a way to
retrieve it. Often, I use `ContextProvider` functions, but this is no different than using a
dataset client. At this level of the architecture, we want to make close to no assumptions
about the behaviors being added to OneML with any kind of plugin. Especially this early in the
life of the project, when we want to be able to explore the problem space in many directions
and as quickly as possible.

```python
class OnemlIoPlugin:
    def on_node_completion(self) -> None:
        """"""


class ExampleIoPlugins(OnemlIoPlugin):
    def on_node_completion(self) -> None:
        # If we want to track all node completions with a dataset commit, we might want to do this:
        self._dataset_client.commit(pipeline, node)

        # Something about node data being written to a standard location and using a plugin to
        # commit it. I don't need to know the node in this case.
        self._local_storage.commit()

        # A plugin that makes a tmp storage location available to nodes can clear it without
        # knowing the node that completed.
        self._tmp_storage.clear()

        # Same with a plugin that maybe gives nodes a way to access secrets without exposing
        # them to other nodes.
        self._secret_manager.clear()
```



```python
"""

"""
DI Containers are specific to the `main` layer of the application, which should only be used for
wiring together library capabilities. This means we should never depend on a specific DI Container,
which we've already removed the need for, by making them all fully private. However, we need to
avoid the Service IDs for the same reason. The DI Container is deciding to fulfill a dependency
with certain Service IDs, and the DI Container will decide to change IDs in order to change
behavior, which leaves libraries unable to expect a specific Service ID to have been used at all.

But we are allowed to reference a few service concepts from library code. A ServiceProvider is just
a callable, without any specific details. I think these are safe to use, but I would try to
only use them within creational classes. A Factory or Builder class is useful to include within a
library because it wraps the concept of creating object from the library, but we can implement
it without details about wiring (I think).

These seem safe to use in libraries:
- ServiceProvider
- ServiceGroupProvider
- ContextProvider
- ContextGroupProvider

I'm a little less certain about a dependency on the ServiceId type, but I haven't needed it yet.
My gut instinct is that we just need to avoid referencing instances of ServiceId (our enums). I
think a good way to separate all the fragile classes is to put these all in one module and
never import this module from the related libraries.

```python
from oneml.services import ServiceId, ContextId, service_provider

class FooServices:
    CAT = ServiceId("cat")
    DOG = ServiceId("dog")


class FooContexts:
    PIPELINE = ContextId[Pipeline]("pipeline")


class FooDiContainer:

    @service_provider(FooServices.CAT)
    def cat(self) -> Cat:
        return Cat()

    @service_provider(FooServices.DOG)
    def dog(self) -> Dog:
        return Dog()
```

In the above example, Pipeline, Cat, and Dog are in library modules; everything else is wiring
and belongs in the `main()` layer. We should never depend on items from `main()` because it's
the outer most layer in our architecture.
"""

""" (dag building api)
I want to do this:
with sdk.open_node(sdk.node("a")) as a:
    a.set_executable(lambda: 1)
with sdk.open_node(sdk.node("b")) as b:
    b.set_executable(lambda: 2)
    # a few options for dependencies
    b.add_dependency(a) maybe? a is immutable here so this is safe, I think
    b.add_dependency(sdk.node("a")) I think I like this one most
    b.add_dependency(b.node("a")) maybe? I think this one is wrong.
    # or some data structure operations? these are all the same
    # skipping ports in the example
    b << a
    sdk.node("a") >> b
    sdk.node("b") << a
    b << sdk.node("a")
"""

"""
Refactoring notes for oneml.io:
in order to decouple the io library from how we decided to wire things together, we should move
the services and di container to the oneml.app package. think of oneml.app as one possible way to
wire together all the pieces, but not the only way. This solidifies the line between oneml, the set
of packages that provide capabilities, and oneml.app, the package that wires them together into an
application that can run pipelines. we can hope to unit test everything very easily in the library
code, but we might have more integration tests in the oneml.app package.
"""

"""
The oneml.services package provides libraries needed to register and initialize services (
objects in the data-structures vs objects dichotomy of Clean Code) used
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

"""
Thoughts:
- making IExecutable be __call__() is not allowed because of limitations in Protocol
- making IExecutable an ABC is not possible because then lambda functions cannot be used
- we might want to maybe rename these kinds of classes `interactors` or `commands`
  - this is more accurate to the name of the relevant design pattern
  - maybe less confusing than exe but command is not much less confusing, is it?
- leaving this API alone for now but I'm not super happy with it
"""

"""
I think it might be useful to think of the execution of pipelines in a similar way to how we think
about kubernetes jobs. We submit a pipeline to run, and can get the details of it with another
call. Our `execute_pipeline()` call is blocking, but it doesn't have to be. For this change we
would just have to change the parameter to be unique and get the name of the pipeline from a
different argument. We can use a request data structure so that we can get a "pod" name
separately from the name used to find a provider in the registry.

- switch session registry to query the service containers directly
  - we can use a static factory method in an ID object to generate namespaced Service IDs
- maybe session providers should not return a session but instead be an executable
  - this allows us to build plugins as executables that run when a session is created
  - for example a plugin that adds debugging nodes to a pipeline in a session
  - can be used as a plugin or as the main "provider"
  - better name for a session provider would be a session builder
    - we have a session builder right now that maybe should turn into something else
    - the old builder could be a slim service provider if we're ok ignoring demeter's law
    - or we can delete the old builder and let the user pick what they need
    - simple use cases can mean I just need a simple dag client
    - complex ones could allow "processor-like" APIs being injected
  - this new API requires us to validate after the execution of the new builder
    - I think this is fine, because the simplest pipeline is at least one node with a node exe
    - this seems pretty trivial to validate in a post-build step before running a pipeline session
    - this also allows plugins again to validate additional, more complex, requirements
    - the only hard-coded requirement we start with is "a valid DAG"
    - plugins can append requirements like "a valid ESLR model experiment"
- we can use `@executable(PipelineBuilderIds.exe_id("hello-world"))`
  - our class that builds a session can be written like a DI Container
  - except instead of providers, we parse all of the executable methods
  - our pipeline registry stores a mapping of these executables
  - we ask the pipeline registry to create a session
  - pipeline registry opens a context, and calls the executable
    - context allows us to trigger an event on context open/close
    - plugins can run code on a session building context open/close event
    - plugins do this with DI Containers and `@group` decorated methods
    - we can create pipeline-specific groups using a static factory method on the ID object
        - `@group(PipelineBuilderId.before("hello-world"))`
        - `@group(PipelineBuilderId.after("hello-world"))`

====================

- think of the dag client as a database connection (to a table)
  - the database connection is your session
  - when you add nodes to the dag client, the nodes are being allocated to the session's dag nodes
- the clients are the database mappers for getting to and modifying a table of entities
  - the dag client is a database mapper for pipeline dags
    - dags are made up of node and edge data structures
    - the dag client allows you to manage nodes and edges
    - we can think of the dag client as the dags table
- a session is a materialization of these tables
  - we can think of the session as the database
"""

"""
Thoughts:
- app just executes an executable/lambda within a context
- the outer context is the app context
- the executable is run inside a pipeline session context
- a pipeline session context just executes frames until the session is completed
- frames run stages of a pipeline session meant to move the status "forward"
- a pipeline session frame can be hard-coded to perform these steps, we can remove the abstraction
- opening the footprint of the session to include the definition of the pipeline has benefits
  - the dag can receive a unique key (the session)
  - the dag can still be derived by a static config, but that is an implementation detail
- does the definnition of the pipeline go into frames? I think so
  - this would allow us to portpone the decision of if we support running multiple pipelines in
  one session
  - we can also postpone deciding how or if we support dynamic pipelines
  - but it blurs our definition of a pipeline
  - alternative is to run multiple sessions with one app
"""


"""
- immunocli tooling should not include argument parsing
- it's about improving on `entrypoint`, not `argparse`
- oneml-pipelines now has a lot of what a good cli tool would provide
- so if we pull that out, then oneml-processors becomes the core oneml piece
"""

"""
Thoughts:
The session is responsible for defining what it means for a pipeline to run. In the session above,
we're just saying that `run()` will execute frames until the state of the pipeline is anything
but "RUNNING". I would like to have a context for the frame, because that will allow me to
implement a full "pipeline replay" that is 100% deterministic, even when our pipelines involve
dataset lookups. If we move the dataset lookups to a "resolution" layer of architecture,
I can cache the results and re-run the pipeline with the same dataset resolution. This also
means that we can completely skip the slowest part of pipeline orchestration right now.
"""
