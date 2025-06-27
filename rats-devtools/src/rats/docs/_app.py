import logging

import click

from rats import apps as apps
from rats import cli as cli
from rats import logs as logs
from rats import projects

logger = logging.getLogger(__name__)


@apps.autoscope
class AppConfigs:
    DOCS_COMPONENT_NAME = apps.ServiceId[str]("docs-component-name.config")
    """
    The name of the component in the repo that contains the mkdocs packages.

    By default, we assume there is a component in the repo named `*devtools*`; but this behavior
    can be replaced by registering a [rats.apps.ContainerPlugin][] to the `rats.docs` python
    entry-point in `pyproject.toml`.

    The final built documentation, created by `rats-docs build`, will be placed in the `dist/site`
    directory within this component.
    """
    MKDOCS_YAML = apps.ServiceId[str]("mkdocs-yaml.config")
    """
    The path to the `mkdocs.yaml` config file, relative to the root of the repo.

    By default, we assume the `mkdocs.yaml` file is in the root directory, but it's sometimes
    preferred to keep it in the docs component, defined by
    [rats.docs.AppConfigs.DOCS_COMPONENT_NAME][].
    """


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        cli.create_group(click.Group("rats-docs"), self).main()

    @cli.command()
    @click.argument("mkdocs-args", nargs=-1)
    def build(self, mkdocs_args: tuple[str, ...]) -> None:
        """Build the mkdocs site for every component in the project."""
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        docs_component = ptools.get_component(self._app.get(AppConfigs.DOCS_COMPONENT_NAME))
        site_dir_path = docs_component.find_path("dist/site")
        config_path = ptools.repo_root() / self._app.get(AppConfigs.MKDOCS_YAML)
        docs_component.run(
            "mkdocs",
            "build",
            "--config-file",
            config_path.as_posix(),
            "--site-dir",
            site_dir_path.as_posix(),
            *mkdocs_args,
        )

    @cli.command()
    @click.argument("mkdocs-args", nargs=-1)
    def serve(self, mkdocs_args: tuple[str, ...]) -> None:
        """Serve the mkdocs site for the project and monitor files for changes."""
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        docs_component = ptools.get_component(self._app.get(AppConfigs.DOCS_COMPONENT_NAME))
        config_path = ptools.repo_root() / self._app.get(AppConfigs.MKDOCS_YAML)
        docs_component.run(
            "mkdocs",
            "serve",
            "--config-file",
            config_path.as_posix(),
            *mkdocs_args,
        )

    @apps.fallback_service(AppConfigs.DOCS_COMPONENT_NAME)
    def _docs_component_name(self) -> str:
        """By default, we make a best guess as to which component has the docs configs."""
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        found = ptools.discover_components()
        for c in found:
            # assume the first component with devtools in the name, as a convention, has mkdocs.
            if "devtools" in c.name:
                return c.name

        # otherwise, we might be a single component repo and the first component is a good guess
        return found[0].name

    @apps.fallback_service(AppConfigs.MKDOCS_YAML)
    def _mkdocs_yaml(self) -> str:
        return "mkdocs.yaml"

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            projects.PluginContainer(self._app),
            apps.PythonEntryPointContainer(self._app, "rats.docs"),
        )


def main() -> None:
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
