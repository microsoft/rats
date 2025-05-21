r"""
A minimal example application that can be submitted as an aml job.

We can run the examples with the cli commands in the [rats_e2e.aml.cli][] module.

```bash
$ python -m rats_e2e.aml.cli --help
Usage: python -m rats_e2e.aml.cli [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  basic-job  Submit the [rats_e2e.aml.basic][] application as an aml job
```

The [rats_e2e.aml.basic.Application][] class contains a small amount of code we want to execute
within an aml job. It outputs information provided to it by the job submitter. We can submit this
job through the `rats-aml submit` cli command, or by using the [rats.aml.submit][] function in
python.

!!! note
    The examples will all run `rats-ci build-image` before any of the example commands to
    make sure the aml job uses the most recent version of our code.

=== "rats-aml submit"
    Submit the basic job, providing additional context defined in a yaml file.

    ```bash
    $ cd rats-devtools
    $ rats-ci build-image && \
        rats-aml submit rats_e2e.aml.basic --wait \
        --context-file src/rats_resources/aml/example-context.yaml
    ```
=== "rats.aml.submit"
    Instead of relying on a static yaml file, we can submit aml jobs with additional control
    using [rats.aml.submit][]. Along with a [rats.app_context.Collection][] instance for the
    remote job, we can specify additional configuration for the creation of the aml job, like the
    aml job environment variables.

    ```python
    from collections.abc import Iterator

    from rats import aml as aml
    from rats import app_context, apps, logs
    from rats_e2e.aml import basic

    class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
        def execute(self) -> None:
            def envs() -> Iterator[dict[str, str]]:
                yield {"RATS_AML_E2E_EXAMPLE": "this env is attached to the remote job"}

            aml.submit(
                "rats_e2e.aml.basic",
                container_plugin=lambda app: apps.StaticContainer(
                    apps.static_group(aml.AppConfigs.CLI_ENVS, envs)
                ),
                context=app_context.Collection.make(
                    app_context.Context.make(
                        basic.AppServices.EXAMPLE_DATA,
                        basic.ExampleData("example data name", "example data value"),
                        basic.ExampleData("another example name", "another example value"),
                    ),
                ),
                wait=True,
            )


    def main() -> None:
        apps.run_plugin(Application)
    ```
    !!! note
        The [rats.aml.AppConfigs][] class contains the complete list of options you can provide
        through the `container_plugin` argument.
=== "src/rats_resources/aml/example-context.yaml"
    We can pass a yaml file to `rats-aml submit` to add [rats.app_context.Context] values
    to the remote aml job, using the `--context-file` argument.
    ```yaml
    items:
      - service_id: ["rats_e2e.aml._example_job:JobServices[example-data]"]
        values:
          - name: example data name
            value: example data name
          - name: another example data name
            value: another example data name
    ```
"""

from ._app import Application, AppServices, ExampleData

__all__ = [
    "AppServices",
    "Application",
    "ExampleData",
]
