import logging
from importlib import resources
from pathlib import Path

import click

from rats import apps as apps
from rats import cli as cli
from rats import logs as logs
from rats import projects
from rats_resources import docs as docs_resources

logger = logging.getLogger(__name__)


@apps.autoscope
class AppConfigs:
    DOCS_COMPONENT_NAME = apps.ServiceId[str]("docs-component-name.config")


@apps.autoscope
class AppServices:
    ROOT_DOCS_PATH = apps.ServiceId[Path]("root-docs-path")


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        cli.create_group(click.Group("rats-docs"), self).main()

    @cli.command()
    def mkdocs_build(self) -> None:
        """Build the mkdocs site for every component in the project."""
        self._do_mkdocs_things("build")

    @cli.command()
    def mkdocs_serve(self) -> None:
        """Serve the mkdocs site for the project and monitor files for changes."""
        self._do_mkdocs_things("serve")

    def _do_mkdocs_things(self, cmd: str) -> None:
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        docs_component = ptools.get_component(self._app.get(AppConfigs.DOCS_COMPONENT_NAME))
        root_docs_path = self._app.get(AppServices.ROOT_DOCS_PATH)

        mkdocs_config = docs_component.find_path("mkdocs.yaml")
        mkdocs_staging_path = docs_component.find_path("dist/docs")
        site_dir_path = docs_component.find_path("dist/site")
        mkdocs_staging_config = docs_component.find_path("dist/mkdocs.yaml")
        # clear any stale state
        docs_component.create_or_empty(mkdocs_staging_path)
        # start with the contents of our root-docs
        docs_component.copy_tree(root_docs_path, mkdocs_staging_path)
        docs_component.symlink(
            # use the README.md at the root as the homepage of the docs site
            ptools.repo_root() / "README.md",
            mkdocs_staging_path / "index.md",
        )
        components = ptools.discover_components()

        for c in components:
            comp_tools = ptools.get_component(c.name)
            docs_path = comp_tools.find_path("docs")
            docs_component.symlink(docs_path, mkdocs_staging_path / c.name)

        # replace the mkdocs config with a fresh version
        mkdocs_staging_config.unlink(missing_ok=True)
        docs_component.copy(mkdocs_config, mkdocs_staging_config)

        args = [
            "--config-file",
            str(mkdocs_staging_config),
        ]
        if cmd == "build":
            args.extend(["--site-dir", str(site_dir_path.resolve())])

        docs_component.run("mkdocs", cmd, *args)

    @apps.fallback_service(AppServices.ROOT_DOCS_PATH)
    def _root_docs_path(self) -> Path:
        """By default, we use the root docs found in rats-devtools unless overwritten."""
        return Path(str(resources.path(docs_resources, "root-docs")))

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

    @apps.container()
    def _plugins(self) -> apps.Container:
        return projects.PluginContainer(self._app)


def main() -> None:
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
