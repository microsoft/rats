import os
from dataclasses import dataclass

from rats import aml, runtime
from rats import apps as apps


@dataclass(frozen=True)
class ExampleData:
    name: str
    value: str


@apps.autoscope
class JobServices:
    EXAMPLE_DATA = apps.ServiceId[ExampleData]("example-data")


class ExampleJob(apps.AppContainer, apps.PluginMixin):
    def execute(self) -> None:
        print("hello, world!")
        context_collection = self._app.get(runtime.AppServices.CONTEXT)
        print("loaded context:")
        for item in context_collection.items:
            print(f"{item.service_id} -> {item.values}")

        job_context = context_collection.decoded_values(
            aml.AmlJobContext,
            aml.AppConfigs.JOB_CONTEXT,
        )
        print(f"aml job context that is always available: {job_context}")

        example_data = context_collection.decoded_values(ExampleData, JobServices.EXAMPLE_DATA)
        print(f"found {len(example_data)} example data item(s) within the context: {JobServices.EXAMPLE_DATA}")
        for x in example_data:
            print(x)

        print("rats envs:")
        for k, v in os.environ.items():
            if k.startswith("RATS_"):
                print(f"{k} → {v}")
