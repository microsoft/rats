# type: ignore[reportUntypedFunctionDecorator]
import logging

from rats import apps, cli, projects

logger = logging.getLogger(__name__)


class PluginCommands(cli.Container):
    _project_tools: apps.Provider[projects.ProjectTools]
    _selected_component: apps.Provider[projects.ComponentTools]
    _devtools_component: apps.Provider[projects.ComponentTools]

    def __init__(
        self,
        project_tools: apps.Provider[projects.ProjectTools],
        selected_component: apps.Provider[projects.ComponentTools],
        devtools_component: apps.Provider[projects.ComponentTools],
    ) -> None:
        self._project_tools = project_tools
        self._selected_component = selected_component
        self._devtools_component = devtools_component

    @cli.command()
    def mkdocs_build(self) -> None:
        """Build the mkdocs site for every component in the project."""
        self._do_mkdocs_things("build")

    @cli.command()
    def mkdocs_serve(self) -> None:
        """Serve the mkdocs site for the project and monitor files for changes."""
        self._do_mkdocs_things("serve")

    def _do_mkdocs_things(self, cmd: str) -> None:
        root_docs_path = self._devtools_component().find_path("src/resources/root-docs")
        mkdocs_config = self._devtools_component().find_path("mkdocs.yaml")
        mkdocs_staging_path = self._devtools_component().find_path("dist/docs")
        site_dir_path = self._devtools_component().find_path("dist/site")
        mkdocs_staging_config = self._devtools_component().find_path("dist/mkdocs.yaml")
        # clear any stale state
        self._devtools_component().create_or_empty(mkdocs_staging_path)
        # start with the contents of our root-docs
        self._devtools_component().copy_tree(root_docs_path, mkdocs_staging_path)
        self._devtools_component().symlink(
            # use the README.md at the root as the homepage of the docs site
            self._project_tools().repo_root() / "README.md",
            mkdocs_staging_path / "index.md",
        )
        components = self._project_tools().discover_components()

        for c in components:
            comp_tools = self._project_tools().get_component(c.name)
            docs_path = comp_tools.find_path("docs")
            self._devtools_component().symlink(docs_path, mkdocs_staging_path / c.name)

        # replace the mkdocs config with a fresh version
        mkdocs_staging_config.unlink(missing_ok=True)
        self._devtools_component().copy(mkdocs_config, mkdocs_staging_config)

        args = [
            "--config-file",
            str(mkdocs_staging_config),
        ]
        if cmd == "build":
            args.extend(["--site-dir", str(site_dir_path.resolve())])

        self._devtools_component().run("mkdocs", cmd, *args)
