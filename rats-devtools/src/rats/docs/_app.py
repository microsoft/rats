import logging
import warnings

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
    The name of the component in the repo that contains `mkdocs.yaml` and dependencies.

    By default, we assume there is a component in the repo named `*devtools*`; but this behavior
    can be replaced by registering a [rats.apps.ContainerPlugin][] to the `rats.docs` pythong
    entry-point in `pyproject.toml`.
    """


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        cli.create_group(click.Group("rats-docs"), self).main()

    @cli.command()
    def _mkdocs_build(self) -> None:
        """
        Build the mkdocs site for every component in the project.

        !!! warning
            This command is deprecated and will be removed in a future release. Use the `build`
            command instead.
        """
        warnings.warn(
            "the `mkdocs-build` command is deprecated. use `build` instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        self.build()

    @cli.command()
    def build(self) -> None:
        """Build the mkdocs site for every component in the project."""
        self._do_mkdocs_things("build")

    @cli.command()
    def _mkdocs_serve(self) -> None:
        """
        Serve the mkdocs site for the project and monitor files for changes.

        !!! warning
            This command is deprecated and will be removed in a future release. Use the `serve`
            command instead.
        """
        warnings.warn(
            "the `mkdocs-serve` command is deprecated. use `serve` instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        self.serve()

    @cli.command()
    def serve(self) -> None:
        """Serve the mkdocs site for the project and monitor files for changes."""
        self._do_mkdocs_things("serve")

    def _do_mkdocs_things(self, cmd: str) -> None:
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        docs_component = ptools.get_component(self._app.get(AppConfigs.DOCS_COMPONENT_NAME))
        root_docs_path = ptools.repo_root() / "docs"

        mkdocs_config = docs_component.find_path("mkdocs.yaml")
        mkdocs_staging_path = docs_component.find_path("dist/docs")
        site_dir_path = docs_component.find_path("dist/site")
        mkdocs_staging_config = docs_component.find_path("dist/mkdocs.yaml")
        # clear any stale state
        docs_component.create_or_empty(mkdocs_staging_path)
        # start with the contents of our root-docs
        docs_component.copy_tree(root_docs_path, mkdocs_staging_path)
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
        return apps.CompositeContainer(
            projects.PluginContainer(self._app),
            apps.PythonEntryPointContainer(self._app, "rats.docs"),
        )


def main() -> None:
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
