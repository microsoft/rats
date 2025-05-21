import os
from dataclasses import dataclass

from rats import aml, runtime
from rats import apps as apps


@dataclass(frozen=True)
class ExampleData:
    name: str
    value: str


@apps.autoscope
class AppServices:
    EXAMPLE_DATA = apps.ServiceId[ExampleData]("example-data")


class Application(apps.AppContainer, apps.PluginMixin):
    """Shows how to read information passed into the application by the aml job submitter."""
    def execute(self) -> None:
        r"""
        Print all the environment and context information in the aml job.

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
            Instead of relying on a static yaml file, we can submit aml jobs with much more control
            using [rats.aml.submit][]. In addition to providing a [rats.app_context.Collection][]
            instance to the remote job, we can specify additional configuration for the creation of
            the aml job, like the aml job environment variables.

            !!! note
                For a complete list of options you can provide through the `container_plugin`
                argument, they are specified in [rats.aml.AppConfigs][].

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
                                basic.ExampleData("another example data name", "another example data value"),
                            ),
                        ),
                        wait=True,
                    )


            def main() -> None:
                apps.run_plugin(Application)
            ```
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
        context_collection = self._app.get(runtime.AppServices.CONTEXT)
        print("loaded context:")
        for item in context_collection.items:
            print(f"{item.service_id} -> {item.values}")

        job_context = context_collection.decoded_values(
            aml.AmlJobContext,
            aml.AppConfigs.JOB_CONTEXT,
        )
        print(f"aml job context that is always available: {job_context}")

        example_data = context_collection.decoded_values(ExampleData, AppServices.EXAMPLE_DATA)
        print(f"found {len(example_data)} example data item(s) within the context: {AppServices.EXAMPLE_DATA}")
        for x in example_data:
            print(x)

        print("rats envs:")
        for k, v in os.environ.items():
            if k.startswith("RATS_"):
                print(f"{k} → {v}")
