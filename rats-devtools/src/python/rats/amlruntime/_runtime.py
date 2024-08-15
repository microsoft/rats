import json
import logging
import time
from collections.abc import Callable, Mapping
from typing import NamedTuple

from azure.ai.ml import MLClient, command
from azure.ai.ml.entities import Environment
from azure.ai.ml.operations import EnvironmentOperations, JobOperations
from azure.ai.ml.operations._run_history_constants import JobStatus, RunHistoryConstants

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
    env_variables: Mapping[str, str]
    workspace: AmlWorkspace
    environment: AmlEnvironment


class AmlRuntime(apps.Runtime):
    """An app runtime that submits jobs to AML for the execution of a set of exes or groups."""

    _ml_client: apps.Provider[MLClient]
    _environment_operations: apps.Provider[EnvironmentOperations]
    _job_operations: apps.Provider[JobOperations]
    _config: apps.Provider[RuntimeConfig]

    def __init__(
        self,
        ml_client: apps.Provider[MLClient],
        environment_operations: apps.Provider[EnvironmentOperations],
        job_operations: apps.Provider[JobOperations],
        config: apps.Provider[RuntimeConfig],
    ) -> None:
        self._ml_client = ml_client
        self._environment_operations = environment_operations
        self._job_operations = job_operations
        self._config = config

    def execute(self, *exe_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        self._run(exe_ids, ())

    def execute_group(self, *exe_group_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        self._run((), exe_group_ids)

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        raise NotImplementedError("not possible! go away!")

    def _run(
        self,
        exe_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
        exe_group_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
    ) -> None:
        config = self._config()
        logger.info(f"{config.environment._asdict()}")

        self._environment_operations().create_or_update(
            Environment(**config.environment._asdict())
        )

        exes_json = json.dumps([exe._asdict() for exe in exe_ids])
        groups_json = json.dumps([group._asdict() for group in exe_group_ids])

        job = command(
            command=config.command,
            compute=config.compute,
            environment=config.environment.full_name,
            environment_variables={
                **config.env_variables,
                "DEVTOOLS_AMLRUNTIME_EXE_IDS": exes_json,
                "DEVTOOLS_AMLRUNTIME_EVENT_IDS": groups_json,
            },
        )
        returned_job = self._job_operations().create_or_update(job)
        logger.info(f"created job: {returned_job.name}")
        self._job_operations().stream(str(returned_job.name))
        logger.info(f"done streaming logs: {returned_job.name}")
        while True:
            job_details = self._job_operations().get(str(returned_job.name))
            logger.info(f"status: {job_details.status}")
            if job_details.status in RunHistoryConstants.TERMINAL_STATUSES:
                break

            logger.warning(f"job {returned_job.name} is not done yet: {job_details.status}")
            time.sleep(2)

        if job_details.status != JobStatus.COMPLETED:
            raise RuntimeError(f"job {returned_job.name} failed with status {job_details.status}")
