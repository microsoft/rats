import os
from dataclasses import dataclass

from rats import aml as aml
from rats import apps, runtime


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
        """Print all the environment and context information in the aml job."""
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
        print(f"{len(example_data)} example data item(s) in context {AppServices.EXAMPLE_DATA}")
        for x in example_data:
            print(x)

        print("rats envs:")
        for k, v in os.environ.items():
            if k.startswith("RATS_"):
                print(f"{k} → {v}")
