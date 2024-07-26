import os
from collections.abc import Callable

from azure.ai.ml import MLClient, command
from azure.ai.ml.entities import Environment
from azure.identity import DefaultAzureCredential

from rats import apps


class AmlRuntime(apps.Runtime):
    def execute(self, *exe_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        print("trying to submit to aml")

        class WorkpsaceInfo:
            def __init__(self):
                self.subscription_id = os.environ.get("DEVTOOLS_AML_SUBSCRIPTION_ID")
                self.resource_group = os.environ.get("DEVTOOLS_AML_RESOURCE_GROUP")
                self.workspace = os.environ.get("DEVTOOLS_AML_WORKSPACE")

        ws_info = WorkpsaceInfo()
        credential = DefaultAzureCredential()
        ml_client = MLClient(
            credential, ws_info.subscription_id, ws_info.resource_group, ws_info.workspace
        )

        pipe_env = Environment(
            image="mcr.microsoft.com/mirror/docker/library/ubuntu:24.04",
            description="A static container image.",
            # How do we make sure this exists and is not created every time?
            name="static-container-image",
            version="2",
        )

        job = command(
            code=None,
            command="echo hello, world",
            environment=pipe_env,
            environment_variables=None,
            compute=os.environ.get("DEVTOOLS_AML_COMPUTE"),
            distribution=None,
            resources=None,
        )

        # submit the command
        returned_job = ml_client.jobs.create_or_update(job)
        # get a URL for the status of the job
        print(returned_job.studio_url)

    def execute_group(self, *exe_group_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        pass

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        raise NotImplementedError("not possible! go away!")
