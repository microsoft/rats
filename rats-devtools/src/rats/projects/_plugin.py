import logging
import os
from pathlib import Path

from rats import apps

from ._component_tools import ComponentTools
from ._project_tools import (
    ComponentNotFoundError,
    ProjectConfig,
    ProjectNotFoundError,
    ProjectTools,
)

logger = logging.getLogger(__name__)


@apps.autoscope
class PluginConfigs:
    """Configurable services within the [rats.projects][] module."""

    PROJECT = apps.ServiceId[ProjectConfig]("project")
    """Main config object to change the behavior of [rats.projects][] libraries."""


@apps.autoscope
class PluginServices:
    """Services made available from the [rats.projects] module."""

    CWD_COMPONENT_TOOLS = apps.ServiceId[ComponentTools]("cwd-component-tools")
    """The component tools instance for the component the command was run within."""
    PROJECT_TOOLS = apps.ServiceId[ProjectTools]("project-tools")
    """Main project library to interact with the repository and the contained components."""

    CONFIGS = PluginConfigs
    """Alias to the [rats.projects.ProjectConfig][] class."""


class PluginContainer(apps.Container, apps.PluginMixin):
    @apps.service(PluginServices.CWD_COMPONENT_TOOLS)
    def _active_component_tools(self) -> ComponentTools:
        ptools = self._app.get(PluginServices.PROJECT_TOOLS)
        cwd = Path().resolve()
        relative = cwd.relative_to(ptools.repo_root()).as_posix()

        if cwd == ptools.repo_root():
            # we're at the root of the repo
            # either this is a single component project, and the devtools component is the only one
            # or we're not in a component and we should use the devtools component by default
            # i'm not sure this is the best and most expected behavior
            # but it lets us run things like the docs tools from the root of a big repo
            return ptools.get_component(ptools.project_name())

        name = relative.split("/")[0]  # the component sits at the root of the project, for now
        return ptools.get_component(name)

    @apps.service(PluginServices.PROJECT_TOOLS)
    def _project_tools(self) -> ProjectTools:
        return ProjectTools(
            # deferring the call to prevent side effects but this api is not great
            config=lambda: self._app.get(PluginServices.CONFIGS.PROJECT),
        )

    @apps.fallback_service(PluginServices.CONFIGS.PROJECT)
    def _project_config(self) -> ProjectConfig:
        repo_root = find_repo_root()
        return ProjectConfig(
            # default to assuming the repo root folder name is the project name
            name=os.environ.get("DEVTOOLS_PROJECT_NAME", repo_root.name),
            path=repo_root.as_posix(),
            image_registry=os.environ.get("DEVTOOLS_IMAGE_REGISTRY", "default.local"),
            image_push_on_build=bool(os.environ.get("DEVTOOLS_IMAGE_PUSH_ON_BUILD", True)),
            # default tag gets calculated from the project hash
            # but this env can be provided by ci pipelines to control the output version
            image_tag=os.environ.get("DEVTOOLS_IMAGE_TAG"),
        )


def find_repo_root(cwd: Path | None = None) -> Path:
    """
    Try to find the path to the root of the repo.

    This method traverses up the directory tree, starting from the working directory, and looks for
    the first directory that contains a `.git` directory. This behavior can be overwritten by
    defining a `DEVTOOLS_PROJECT_ROOT` environment variable.

    Args:
        cwd: optionally provide a starting search directory
    """
    env = os.environ.get("DEVTOOLS_PROJECT_ROOT")
    if env:
        return Path(env)

    if cwd is None:
        cwd = Path.cwd()

    guess = cwd.resolve()
    while str(guess) != "/":
        if (guess / ".git").exists():
            return guess
        guess = guess.parent

    raise ProjectNotFoundError(
        "repo root not found. devtools must be used on a project in a git repo."
    )


def find_nearest_component(cwd: Path | None = None) -> Path:
    """
    Try to find the path to the root of the nearest component.

    This method traverses up the directory tree, starting from the working directory, and looks for
    the first directory that contains a `pyproject.toml` file.

    Args:
        cwd: optionally provide a starting search directory
    """
    if cwd is None:
        cwd = Path.cwd()

    guess = cwd.resolve()
    while str(guess) != "/":
        if (guess / "pyproject.toml").exists() and (guess / "pyproject.toml").is_file():
            return guess
        guess = guess.parent

    raise ComponentNotFoundError(f"component root not found from cwd: {cwd.as_posix()}.")
