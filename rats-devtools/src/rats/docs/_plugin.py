import logging
from collections.abc import Iterator
from pathlib import Path

import click
from importlib import resources

from rats import apps as apps
from rats import cli as cli
from rats import devtools, projects
from rats_resources import docs as docs_resources

from ._commands import PluginCommands

logger = logging.getLogger(__name__)


@apps.autoscope
class PluginConfigs:
    DOCS_COMPONENT = apps.ServiceId[str]("docs-component.config")


@apps.autoscope
class PluginServices:
    COMMANDS = apps.ServiceId[cli.Container]("commands")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")
    ROOT_DOCS_PATH = apps.ServiceId[Path]("root-docs-path")


class PluginContainer(apps.Container, apps.PluginMixin):
    @apps.group(devtools.AppServices.ON_REGISTER)
    def _on_open(self) -> Iterator[apps.Executable]:
        yield apps.App(
            lambda: cli.attach(
                self._app.get(devtools.AppServices.MAIN_CLICK),
                self._app.get(PluginServices.MAIN_CLICK),
            )
        )

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.Container:
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        return PluginCommands(
            project_tools=lambda: self._app.get(projects.PluginServices.PROJECT_TOOLS),
            selected_component=lambda: self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS),
            docs_component=lambda: ptools.get_component(self._app.get(PluginConfigs.DOCS_COMPONENT)),
            root_docs_path=self._app.get(PluginServices.ROOT_DOCS_PATH),
        )

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        return cli.create_group(
            click.Group(
                "docs",
                help="commands to help author docs-as-code",
            ),
            self._app.get(PluginServices.COMMANDS),
        )

    @apps.fallback_service(PluginServices.ROOT_DOCS_PATH)
    def _root_docs_path(self) -> Path:
        """By default, we use the root docs found in rats-devtools unless overwritten."""
        return Path(str(resources.path(docs_resources, "root-docs")))

    @apps.fallback_service(PluginConfigs.DOCS_COMPONENT)
    def _docs_component(self) -> str:
        """By default, we make a best guess as to which component has the docs configs."""
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        found = ptools.discover_components()
        for c in found:
            # assume the first component with devtools in the name, as a convention, has mkdocs.
            if "devtools" in c.name:
                return c.name

        # otherwise, we might be a single component repo and the first component is a good guess
        return found[0].name
