# Dagster

We installed dagster and dagit into rats-app in order to evaluate its features and compare them to
our plans for rats.

## Dependencies

The `dagster` package had 14 dependencies, a few of which caused concerns.

```
Package operations: 13 installs, 2 updates, 0 removals

• Updating grpcio (1.51.1 -> 1.48.0)
• Installing fsspec (2023.1.0)
• Installing humanfriendly (10.0)
• Installing pytzdata (2020.1)
• Updating sqlalchemy (2.0.0 -> 1.4.46)
• Installing coloredlogs (14.0)
• Installing croniter (1.3.8)
• Installing docstring-parser (0.15)
• Installing grpcio-health-checking (1.43.0)
• Installing pendulum (2.1.2)
• Installing python-dotenv (0.21.1)
• Installing tabulate (0.9.0)
• Installing toposort (1.9)
• Installing universal-pathlib (0.0.21)
• Installing dagster (1.1.14)
```

- `sqlalchemy` was downgraded from 2.0.0 to 1.4.46. This is a major version downgrade.
- `python-dotenv` has a possibility of altering the global environment variables in our code.
- `coloredlogs` is typically a development dependency and might conflict with immunocli.

The `dagit` package had 19 dependencies. Nothing stood out as a concern.

```
Package operations: 20 installs, 0 updates, 0 removals

• Installing graphql-core (3.2.3)
• Installing multidict (6.0.4)
• Installing sniffio (1.3.0)
• Installing aniso8601 (9.0.1)
• Installing anyio (3.6.2)
• Installing backoff (2.2.1)
• Installing graphql-relay (3.2.0)
• Installing requests-toolbelt (0.10.1)
• Installing yarl (1.8.2)
• Installing gql (3.4.0)
• Installing graphene (3.2.1)
• Installing h11 (0.14.0)
• Installing httptools (0.5.0)
• Installing starlette (0.23.1)
• Installing uvloop (0.17.0)
• Installing watchfiles (0.18.1)
• Installing websockets (10.4)
• Installing dagster-graphql (1.1.14)
• Installing uvicorn (0.20.0)
• Installing dagit (1.1.14)
```

## Hello World

I tried to create a simple step that logged information and produced no data. Following the example
at https://docs.dagster.io/getting-started/hello-dagster, I was able to materialize my step, but it
wasn't clear how to re-run it after modifying the code, and I was not able to find the output from
the step in the `dagit` UI or the terminal. Looks like dagster logging is completely separated from
the python logging configuration. Dagit captured some of my output and made it available in the UI.

Dagit captured the logs from my step and wrote it to a flat file. I would want to see how much this
can be disabled so we can leverage our central logging tooling.

## "Real" Example

I wanted to write a small pipeline that ran executables that were defined in a decoupled fashion.
My blind implementation and using `materialize()` manually led to a working pipeline, which was
great:

```python
class Presenter:
    def publish(self, thing: str) -> None:
        logger.warning(thing)


class GenerateThings:
    _out: Presenter

    def __init__(self, out: Presenter) -> None:
        self._out = out

    def execute(self) -> None:
        self._out.publish(str(uuid.uuid4()))


if __name__ == "__main__":
    presenter = Presenter()
    steps = GenerateThings(presenter)
    materialize([asset(steps.execute)])
```

- I'm not sure how to wire the input/output from steps when we don't use the mapping of the method
  argument names.

I tried to make an adapter to properly handle the input/output interface for dagster but ran into
some issues:

```python
class Presenter:
    _results: list[str]

    def __init__(self) -> None:
        self._results = []

    def publish(self, thing: str) -> None:
        logger.warning(thing)
        self._results.append(thing)

    def get_latest(self) -> str:
        return self._results[-1]


class GenerateThings:
    _out: Presenter

    def __init__(self, out: Presenter) -> None:
        self._out = out

    def execute(self) -> None:
        self._out.publish(str(uuid.uuid4()))


class Adapter:
    _command: GenerateThings
    _presenter: Presenter

    def __init__(self, command: GenerateThings, presenter: Presenter) -> None:
        self._command = command
        self._presenter = presenter

    def generate_things(self) -> str:
        self._command.execute()
        return self._presenter.get_latest()


if __name__ == "__main__":
    data = Presenter()
    steps = GenerateThings(data)
    adapter = Adapter(steps, data)
    materialize([asset(adapter.generate_things)])
```

- This runs fine as a script, but I cannot point my dagit instance at this file because it does not
  find any of the assets.
- We cannot use the `asset()` decorator on a class method because it gets confused by the `self`
  argument.

> /home/lopisani/.../dagster/_core/workspace/context.py:588:
> UserWarning: Error loading repository location
> _main.py:dagster._core.errors.DagsterInvariantViolationError:
> No repositories, jobs, pipelines, graphs, asset groups, or asset definitions found in "_main".
