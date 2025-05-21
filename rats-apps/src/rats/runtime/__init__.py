"""
Run rats applications, providing external context.

The provided `rats-runtime` cli allows the registration and execution of [rats.apps.AppContainer][]
applications. Register to the python plugin group called `rats.runtime.apps`, and list available
plugins with `rats-runtime list`.

```toml title="pyproject.toml"
[project.entry-points."rats.runtime.apps"]
"rats_e2e.runtime" = "rats_e2e.runtime:Application"
```

We register an example application you can run with `rats-runtime run rats_e2e.runtime`. The name
of the registered entry point in your `pyproject.toml` will map to the name provided to
`rats-runtime run`.

```bash
$ rats-runtime run rats_e2e.runtime
hello, world!
looking for any registered context: rats_e2e.runtime._app:AppServices[example-data]
```

Our example application looks for any context services, which can be provided to the `run` command.

=== "/code"
    ```bash
    $ rats-runtime run \
        rats_e2e.runtime \
        --context-file src/rats_resources/runtime/example-context.yaml
    hello, world!
    looking for any registered context: rats_e2e.runtime._app:AppServices[example-data]
    found example data element: ExampleData(id='111', thing_a='111', thing_b='111')
    found example data element: ExampleData(id='222', thing_a='222', thing_b='222')
    ```
=== "src/rats_resources/runtime/example-context.yaml"
    ```yaml
    --8<-- "rats_resources/runtime/example-context.yaml"
    ```
=== "src/rats_e2e/runtime/_app.py"
    ```python
    --8<-- "rats_e2e/runtime/_app.py"
    ```
=== "src/rats_e2e/runtime/_data.py"
    ```python
    --8<-- "rats_e2e/runtime/_data.py"
    ```

!!! info
    Most users won't typically use `rats-runtime` directly, but this interface is used by other
    abstractions to execute applications remotely, like the [rats.aml][] module, adding the ability
    to execute applications within an azure ml job.
"""

from ._app import Application, AppServices, main
from ._request import DuplicateRequestError, Request, RequestNotFoundError

__all__ = [
    "AppServices",
    "Application",
    "DuplicateRequestError",
    "Request",
    "RequestNotFoundError",
    "main",
]
