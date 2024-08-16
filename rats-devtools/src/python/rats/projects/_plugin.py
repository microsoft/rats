import logging
import os
from pathlib import Path

from rats import apps
from rats import projects as projects

from ._component_tools import ComponentTools
from ._project_tools import ProjectConfig, ProjectNotFoundError, ProjectTools

logger = logging.getLogger(__name__)


@apps.autoscope
class PluginConfigs:
    PROJECT = apps.ServiceId[ProjectConfig]("project")


@apps.autoscope
class PluginServices:
    CWD_COMPONENT_TOOLS = apps.ServiceId[ComponentTools]("cwd-component-tools")
    DEVTOOLS_COMPONENT_TOOLS = apps.ServiceId[ComponentTools]("devtools-component-tools")
    PROJECT_TOOLS = apps.ServiceId[ProjectTools]("project-tools")

    CONFIGS = PluginConfigs

    @staticmethod
    def component_tools(name: str) -> apps.ServiceId[ComponentTools]:
        return apps.ServiceId[ComponentTools](f"component-tools[{name}]")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.CWD_COMPONENT_TOOLS)
    def _active_component_tools(self) -> ComponentTools:
        ptools = self._app.get(PluginServices.PROJECT_TOOLS)
        name = Path().resolve().name
        return ptools.get_component(name)

    @apps.service(PluginServices.DEVTOOLS_COMPONENT_TOOLS)
    def _devtools_component_tools(self) -> ComponentTools:
        project = self._app.get(PluginServices.PROJECT_TOOLS)
        return self._app.get(
            projects.PluginServices.component_tools(project.devtools_component().name),
        )

    @apps.service(PluginServices.PROJECT_TOOLS)
    def _project_tools(self) -> ProjectTools:
        return ProjectTools(
            # deferring the call to prevent side effects but this api is not great
            config=lambda: self._app.get(PluginServices.CONFIGS.PROJECT),
        )

    @apps.fallback_service(PluginServices.CONFIGS.PROJECT)
    def _project_config(self) -> ProjectConfig:
        repo_root = str(find_repo_root())
        return ProjectConfig(
            name=os.environ.get("DEVTOOLS_PROJECT_NAME", "default-project"),
            path=repo_root,
            image_registry=os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local"),
            image_push_on_build=True,
        )


def find_repo_root() -> Path:
    env = os.environ.get("DEVTOOLS_PROJECT_ROOT")
    if env:
        return Path(env)

    guess = Path().resolve()
    while str(guess) != "/":
        if (guess / ".git").exists():
            return guess
        guess = guess.parent

    raise ProjectNotFoundError(
        "repo root not found. devtools must be used on a project in a git repo."
    )
