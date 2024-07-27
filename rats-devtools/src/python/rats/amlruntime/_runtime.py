import logging
from collections.abc import Callable
from typing import NamedTuple

from azure.ai.ml import MLClient, command
from azure.ai.ml.entities import Environment
from azure.ai.ml.operations import EnvironmentOperations, JobOperations

from rats import apps

logger = logging.getLogger(__name__)


class AmlWorkspace(NamedTuple):
    subscription_id: str
    resource_group_name: str
    workspace_name: str


class AmlEnvironment(NamedTuple):
    name: str
    image: str
    version: str

    @property
    def full_name(self) -> str:
        return f"{self.name}:{self.version}"


class RuntimeConfig(NamedTuple):
    command: str
    compute: str
    workspace: AmlWorkspace
    environment: AmlEnvironment


class AmlRuntime(apps.Runtime):
    _ml_client: MLClient
    _environment_operations: EnvironmentOperations
    _job_operations: JobOperations
    _config: apps.ConfigProvider[RuntimeConfig]

    def __init__(
        self,
        ml_client: MLClient,
        environment_operations: EnvironmentOperations,
        job_operations: JobOperations,
        config: apps.ConfigProvider[RuntimeConfig],
    ) -> None:
        self._ml_client = ml_client
        self._environment_operations = environment_operations
        self._job_operations = job_operations
        self._config = config

    def execute(self, *exe_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        config = self._config()
        logger.info("trying to submit to aml")

        self._environment_operations.create_or_update(Environment(**config.environment._asdict()))

        job = command(
            command=config.command,
            compute=config.compute,
            environment=config.environment.full_name,
        )
        returned_job = self._job_operations.create_or_update(job)
        logger.info(returned_job.studio_url)

    def execute_group(self, *exe_group_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        pass

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        raise NotImplementedError("not possible! go away!")
