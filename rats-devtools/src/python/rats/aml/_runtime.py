from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import NamedTuple

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


class AmlConfig(NamedTuple):
    compute: str
    outputs: Mapping[str, AmlIO]
    inputs: Mapping[str, AmlIO]
    workspace: AmlWorkspace
    environment: AmlEnvironment
