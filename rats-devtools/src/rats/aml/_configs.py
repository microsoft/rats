from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import NamedTuple

logger = logging.getLogger(__name__)


class AmlWorkspace(NamedTuple):
    """The aml workspace used for submitted aml jobs."""

    subscription_id: str
    """Azure subscription containing the desired workspace."""
    resource_group_name: str
    """Azure resource group containing the desired workspace."""
    workspace_name: str
    """Azure aml workspace name jobs should be submitted to."""


class AmlBuildContext(NamedTuple):
    dockerfile_path: str | None
    path: str | None


class AmlEnvironment(NamedTuple):
    """The details of the AML Environment being used by an aml job."""

    name: str
    """
    The name of the built environment in AML.

    Often, this is the name of the component since rats typically has a 1:1 relationship between
    components and docker images. These environments are discoverable in the AML workspace and
    each environment can have many versions.
    """
    image: str | None
    """
    The full name, with registry and tag, of the container image for this environment.

    In the AML workspace, this is shown as the "Docker image". In rats, we typically build
    a full image using the standard tools like Docker, and have AML use the built images without
    making any runtime modifications to it. This ensures the images we build in CI pipelines are
    used without modifications after they have been tested (by you).

    Mutually exclusive with "build".
    """
    version: str
    """
    The version of the environment being used for AML jobs.

    Typically, this matches the tag portion of the built container images. You will find a version
    drop-down when viewing the environment in your AML workspace.
    """
    build: AmlBuildContext | None
    """
    Docker build context for the environment.
    This is used when the environment is built by AML. Mutually exclusive with "image".
    """

    @property
    def full_name(self) -> str:
        """
        The AML environment and version.

        Unlike the [AmlEnvironment.image][rats.aml.AmlEnvironment.image] property, this is the
        full name of the AML environment, and not the container image. In most cases, this is the
        name of the component, and the container tag, but does not contain the registry
        information. This is a unique identifier within your AML workspace, but not globally,
        like container images.
        """
        return f"{self.name}:{self.version}"


class AmlIO(NamedTuple):
    type: str
    path: str
    mode: str


class AmlJobDetails(NamedTuple):
    compute: str
    inputs: dict[str, AmlIO]  # avoiding the more correct Mapping because of dataclass_wizard
    outputs: dict[str, AmlIO]  # avoiding the more correct Mapping because of dataclass_wizard
    workspace: AmlWorkspace
    environment: AmlEnvironment


@dataclass(frozen=True)
class AmlJobContext:
    """Context added by default to all aml jobs with values used by [rats.aml][]."""

    uuid: str
    """A unique id tied to a given submission of an aml job."""

    job_details: AmlJobDetails
    """The compute, workspace, environment, and input/outputs for the aml job."""
