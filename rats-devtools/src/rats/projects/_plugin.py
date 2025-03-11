import logging
import os
from pathlib import Path

from rats import apps

from ._component_tools import ComponentTools
from ._project_tools import ProjectConfig, ProjectNotFoundError, ProjectTools

logger = logging.getLogger(__name__)


@apps.autoscope
class PluginConfigs:
    PROJECT = apps.ServiceId[ProjectConfig]("project")


@apps.autoscope
class PluginServices:
    CWD_COMPONENT_TOOLS = apps.ServiceId[ComponentTools]("cwd-component-tools")
    PROJECT_TOOLS = apps.ServiceId[ProjectTools]("project-tools")

    CONFIGS = PluginConfigs


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
            return ptools.get_component(cwd.name)

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
        repo_root = str(find_repo_root())
        return ProjectConfig(
            name=os.environ.get("DEVTOOLS_PROJECT_NAME", "default-project"),
            path=repo_root,
            image_registry=os.environ.get("DEVTOOLS_IMAGE_REGISTRY", "default.local"),
            image_push_on_build=bool(os.environ.get("DEVTOOLS_IMAGE_PUSH_ON_BUILD", True)),
            # default tag gets calculated from the project hash
            # but this env can be provided by ci pipelines to control the output version
            image_tag=os.environ.get("DEVTOOLS_IMAGE_TAG"),
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
