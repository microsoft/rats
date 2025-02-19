from __future__ import annotations

import json
import logging
import time
from collections.abc import Mapping
from typing import TYPE_CHECKING, NamedTuple

from rats import apps

if TYPE_CHECKING:
    from azure.ai.ml.operations import EnvironmentOperations, JobOperations

logger = logging.getLogger(__name__)


class AmlWorkspace(NamedTuple):
    subscription_id: str
    resource_group_name: str
    workspace_name: str


class AmlEnvironment(NamedTuple):
    name: str
    """
    The name of the built environment in AML.

    Often, this is the name of the component since rats typically has a 1:1 relationship between
    components and docker images. These environments are discoverable in the AML workspace and
    each environment can have many versions.
    """
    image: str
    """
    The full name, with registry and tag, of the container image for this environment.

    In the AML workspace, this is shown as the "Docker image" and is sometimes used as the parent
    image when asking AML to build the environment for us. However, in rats, we typically build
    a full image using the standard tools like Docker, and have AML use the built images without
    making any runtime modifications to it. This ensures the images we build in CI pipelines are
    used without modifications after they have been tested (by you).
    """
    version: str
    """
    The version of the environment being used for AML jobs.

    Typically, this matches the tag portion of the built container images. You will find a version
    drop-down when viewing the environment in your AML workspace.
    """

    @property
    def full_name(self) -> str:
        """
        The AML environment and version.

        Unlike the [AmlEnvironment.image][] property, this is the full name of the AML environment,
        and not the container image. In most cases, this is the name of the component, and the
        container tag, but does not contain the registry information. This is a unique identifier
        within your AML workspace, but not globally, like container images.
        """
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


class Runtime(apps.Runtime):
    """An app runtime that submits jobs to AML for the execution of a set of exes or groups."""

    _environment_operations: apps.Provider[EnvironmentOperations]
    _job_operations: apps.Provider[JobOperations]
    _config: apps.Provider[RuntimeConfig]

    def __init__(
        self,
        environment_operations: apps.Provider[EnvironmentOperations],
        job_operations: apps.Provider[JobOperations],
        config: apps.Provider[RuntimeConfig],
    ) -> None:
        self._environment_operations = environment_operations
        self._job_operations = job_operations
        self._config = config

    def execute(self, *exe_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        self._run(exe_ids, ())

    def execute_group(self, *exe_group_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        self._run((), exe_group_ids)

    def _run(
        self,
        exe_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
        exe_group_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
    ) -> None:
        from azure.ai.ml import Input, Output, command
        from azure.ai.ml.entities import Environment
        from azure.ai.ml.operations._run_history_constants import JobStatus, RunHistoryConstants

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
