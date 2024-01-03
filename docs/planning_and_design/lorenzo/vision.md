# Services, Objects, Data Structures, Contexts, etc.

!!! abstract
    These are mostly ramblings about patterns, and how they could be used to build clean user APIs.

## Providers

Providers are objects that return another object; they are callable and take no arguments from
the user. Providers are valuable without input
arguments because they allow authors to give users access to cababilities without exposing any
of the details of how to initialize any of the class instances. The DI Container is a registry
to give users a simple way to access/call providers; and interact with the desired capabilities.
DI
Containers and Providers belong to portion of the software architecture responsible for
accessing capabilities. The capabilities are represented by objects – the ones that are
returned by providers.

!!! example "Example Database Client"
    A database client might allow users to run SQL queries against a database. This object
    needs to be initialized with valid credentials, but we don't want to require users to know
    how to configure these credentials, so we create a provider that returns a database client.
    The provider is responsible for initializing the database client with the right credentials;
    and we can register this provider into a DI Container in order for users to access the database
    client in the same way they access any other capability.

    ```python
    class DatabaseClient:
        def __init__(self, host: str, port: int, username: str, password: str) -> None:
            self._host = host
            self._port = port
            self._username = username
            self._password = password

        def run_query(self, query: str):
            # run query against database
            pass

    def database_client_provider() -> DatabaseClient:
        return DatabaseClient(
            host='localhost',
            port=5432,
            username='postgres',
            password='postgres',
        )

    container = ServiceContainer()
    container.register_provider(
        ServiceId[DatabaseClient]("database-client"),
        database_client_provider,
    )
    ```

## Executables

Executables are objects that perform an operation. Instead of returning capabilities, like
providers, executables leverage capabilities in order to expose the same 0-argument interface as
providers, but without a return value. A user of an executable does not need to know the
details of creating a spark cluster in order to request a cluster be created. In many cases,
the values needed to create a spark cluster, and the UI for defining these values, is not
interesting to the user. I think executables are most valuable as a very high level abstraction
for the core responsibilities of the system.

!!! example "Example Executables"
    The package, `immunodata.spark_examples`, provides an executable for `create_cluster()`,
    `list_clusters()`, and a `delete_cluster()`. Unfortunately, we don't know, at this point,
    which parameters of a cluster are interesting to the user; but I am certain that there is
    at least one person interested in each and every permutation of required and optional
    cluster arguments; some will want to provide a user email to track along with the cluster
    usage; some will ask you to populate that field based on the user's current azure cli
    profile. Making this assumption avoids us going through the futile excercise of trying to
    group sets of cluster arguments into things our flawed notion of a persona might find
    interesting, we can call those details private, and puntable, and stick with the simpler, more
    obvious use case; our users want to create spark clusters.

    The executables above form the shortest elevator pitch for your software. The next layer of
    abstraction below us will start to define how the user requests a cluster, and how they can
    customize their experience. This might be a web panel, a desktop client, or a cli, but
    those details are not part of our elevator pitch.

### CLI Commands

A lot of the CLI Commands we develop represent an operation we wanted to expose to the user
through a terminal. It's relatively easy to create a new command, define the required arguments,
and access the user's input through a request object. We defined a persona that wanted to
author terminal commands, and developed a library for doing just that.

!!! example "Example CLI Command"

    ```python
    class CreateClusterCommand(CliCommand):
        command_name = "create-cluster"

        def configure_parser(self, parser: ArgumentParser) -> None:
            parser.add_argument("cluster-name")

        def execute(self, request: CliRequest) -> None:
            print(f"creating cluster named: {request.get('cluster-name')")
    ```

After using this library successfully for a while, we defined a new persona. Sometimes, users
want to be able to call CLI Commands from other parts of code; but our API is very tightly
coupled to the terminal. Users can use a subprocess to execute desired CLI Commands, but that
would never be the ideal API we would have developed if this persona was our first customer.
Besides the awkwardness of using a subprocess, we also have conflicting demands about the
arguments the two personas requested. One simple shortcut is to make the CLI Command expose
arguments for everything, and make them all optional. But this is also not the API we would
develop if the requests weren't related. So instead of making everything optional, let's take
the opposite extreme and turn these CLI Commands into Executables, by removing all their input
arguments, and eliminating the decision of where the values might come from.

!!! example "Example CLI Command as Executable"

    ```python
    class CreateClusterExecutable:

        def __init__(self, request: ClusterRequest) -> None:
            self._request = request

        def execute(self) -> None:
            print(f"creating cluster named: {self._request.cluster_name})")
    ```

    At this level of abstraction, we don't want to worry about how the configuration values for
    the cluster is built. We only want to define the values we need for the creation of the
    cluster.

    ```python
    class ClusterRequest(NamedTuple):
        name: str
        cpu_cores: int
        memory: int
    ```

====== More Rambly ======
```python
cit = Context[ClusterRequest]("cli-command.create-cluster")

class SomeUseCases:

    def __init__(self, ctx: ContextClient) -> None:
        self._ctx = ctx

    @executable(ExeId("create-cluster"), context=cit)
    def create_cluster(self) -> None:
        values = self._ctx.get_context(cit)
        print(f"creating cluster named: {values.name})")


with r.open(cit, ClusterRequest(
        name="example-cluster",
        cpu_cores=4,
        memory=100,
    )):
    exe.execute()
```

Last bit! We can now hide all this flexibility and expose perfect APIs to our two personas.

```python
class PersonaA:

    def create_cluster(self, name: str) -> None:
        with r.open(cit, ClusterRequest(
            name=f"jupyter-{name}",
            # Get below values… from somewhere else
            cpu_cores=4,
            memory=50,
        )):
            self.exe.execute()

        CreateClusterExecutable(...).execute()


class PersonaB:

    def create_cluster(self, cpu_cores: int) -> None:
        with r.open(cit, ClusterRequest(
            cpu_cores=cpu_cores,
            # Get below values… from somewhere else
            name=f"workflow-{uuid}",
            memory=50,
        )):
            self.exe.execute()
```

- the foundational layer allows us to expose the perfect API
- instead of making everything optional, remove arguments
- give users hand-crafted APIs that expose just the interface they care about
- automate aware the boring wiring of contexts to executables
