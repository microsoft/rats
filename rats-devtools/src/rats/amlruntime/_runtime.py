import json
import logging
import time
from collections.abc import Callable, Mapping
from typing import NamedTuple, cast

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


class AmlIO(NamedTuple):
    type: str
    path: str
    mode: str


class RuntimeConfig(NamedTuple):
    command: str
    compute: str
    env_variables: Mapping[str, str]
    outputs: Mapping[str, AmlIO]
    inputs: Mapping[str, AmlIO]
    workspace: AmlWorkspace
    environment: AmlEnvironment


class AmlRuntime(apps.Runtime):
    """An app runtime that submits jobs to AML for the execution of a set of exes or groups."""

    _environment_operations: apps.Provider["EnvironmentOperations"]  # type: ignore[reportUndefinedVariable]  # noqa: F821
    _job_operations: apps.Provider["JobOperations"]  # type: ignore[reportUndefinedVariable]  # noqa: F821
    _config: apps.Provider[RuntimeConfig]

    def __init__(
        self,
        environment_operations: apps.Provider["EnvironmentOperations"],  # type: ignore[reportUndefinedVariable]  # noqa: F821
        job_operations: apps.Provider["JobOperations"],  # type: ignore[reportUndefinedVariable]  # noqa: F821
        config: apps.Provider[RuntimeConfig],
    ) -> None:
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
        from azure.ai.ml import Input, Output, command  # type: ignore[reportUnknownVariableType]
        from azure.ai.ml.entities import Environment, Job
        from azure.ai.ml.operations import EnvironmentOperations, JobOperations
        from azure.ai.ml.operations._run_history_constants import JobStatus, RunHistoryConstants

        config = self._config()
        logger.info(f"{config.environment._asdict()}")

        env_ops: EnvironmentOperations = self._environment_operations()  # type: ignore[reportUnknownVariableType]
        job_ops: JobOperations = self._job_operations()  # type: ignore[reportUnknownVariableType]

        env_ops.create_or_update(  # type: ignore[reportUnknownMemberType]
            Environment(**config.environment._asdict())
        )

        exes_json = json.dumps([exe._asdict() for exe in exe_ids])
        groups_json = json.dumps([group._asdict() for group in exe_group_ids])

        job = command(
            command=config.command,
            compute=config.compute,
            environment=config.environment.full_name,
            outputs={
                k: Output(type=v.type, path=v.path, mode=v.mode) for k, v in config.outputs.items()
            },
            inputs={
                k: Input(type=v.type, path=v.path, mode=v.mode) for k, v in config.inputs.items()
            },
            environment_variables={
                # we always define the two devtools envs and let the user define others
                **config.env_variables,
                "DEVTOOLS_EXE_IDS": exes_json,
                "DEVTOOLS_EVENT_IDS": groups_json,
            },
        )

        returned_job: Job = cast(Job, job_ops.create_or_update(job))  # type: ignore[reportUnknownMemberType]
        logger.info(f"created job: {returned_job.name!s}")
        job_ops.stream(str(returned_job.name))  # type: ignore[reportUnknownMemberType]
        logger.info(f"done streaming logs: {returned_job.name}")
        while True:
            job_details: Job = job_ops.get(str(returned_job.name))  # type: ignore[reportUnknownVariableType]
            logger.info(f"status: {job_details.status!s}")  # type: ignore[reportUnknownMemberType]
            if job_details.status in RunHistoryConstants.TERMINAL_STATUSES:  # type: ignore[reportUnknownMemberType]
                break

            logger.warning(f"job {returned_job.name} is not done yet: {job_details.status}")  # type: ignore[reportUnknownMemberType]
            time.sleep(2)

        if job_details.status != JobStatus.COMPLETED:  # type: ignore[reportUnknownMemberType]
            raise RuntimeError(f"job {returned_job.name} failed with status {job_details.status}")  # type: ignore[reportUnknownMemberType]
