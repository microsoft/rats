# type: ignore[reportUntypedFunctionDecorator]
import logging

from rats import cli, projects

logger = logging.getLogger(__name__)


class PluginCommands(cli.CommandContainer):
    _project_tools: projects.ProjectTools
    _selected_component: projects.ComponentTools
    _devtools_component: projects.ComponentTools

    def __init__(
        self,
        project_tools: projects.ProjectTools,
        selected_component: projects.ComponentTools,
        devtools_component: projects.ComponentTools,
    ) -> None:
        self._project_tools = project_tools
        self._selected_component = selected_component
        self._devtools_component = devtools_component

    @cli.command()
    def sphinx_apidoc(self) -> None:
        """Build the sphinx apidoc for the package, saving output in dist/sphinx-apidoc."""
        # devtools package has the sphinx config files
        sphinx_resources_path = self._devtools_component.find_path("resources/sphinx-docs")
        # we place the built documentation in the component we are building
        component_apidoc_path = self._selected_component.find_path("dist/sphinx-apidoc")

        self._selected_component.create_or_empty(component_apidoc_path)
        # copy the config files from the devtools package into the component we are building
        self._selected_component.copy_tree(sphinx_resources_path, component_apidoc_path)

        src_prefix = (
            # hackily only support src/ and src/python structures for now
            "src/python" if self._selected_component.find_path("src/python").is_dir() else "src"
        )

        self._selected_component.run(
            "sphinx-apidoc",
            "--doc-project",
            self._project_tools.project_name(),
            "--tocfile",
            "index",
            "--implicit-namespaces",
            "--module-first",
            "--force",
            "--output-dir",
            str(component_apidoc_path),
            "--templatedir",
            str(component_apidoc_path / "_templates"),
            *[f"{src_prefix}/{p.name}" for p in self._selected_component.discover_root_packages()],
        )

    @cli.command()
    def sphinx_markdown(self) -> None:
        """
        Convert the sphinx apidoc to markdown, saving output in docs/api.

        This command should be run after sphinx-apidoc, and before mkdocs-build. We convert the
        sphinx apidoc to markdown so that it can be rendered and indexed alongside the rest of the
        other documentation.
        """
        dist_md_path = self._selected_component.find_path("dist/sphinx-markdown")
        api_docs_path = self._selected_component.find_path("docs/api")
        self._selected_component.create_or_empty(dist_md_path)
        self._selected_component.run(
            "sphinx-build",
            "-M",
            "markdown",
            "dist/sphinx-apidoc",
            "dist/sphinx-markdown",
        )
        # empty the docs/api directory from previous runs, except the .gitignore file
        # this can probably be done more elegantly
        gitignore = (api_docs_path / ".gitignore").read_text()
        self._selected_component.create_or_empty(api_docs_path)
        (api_docs_path / ".gitignore").write_text(gitignore)

        self._selected_component.copy_tree(dist_md_path / "markdown", api_docs_path)

    @cli.command()
    def mkdocs_build(self) -> None:
        """Build the mkdocs site for every component in the project."""
        self._do_mkdocs_things("build")

    @cli.command()
    def mkdocs_serve(self) -> None:
        """
        Serve the mkdocs site for the project and monitor files for changes.

        This command does not automatically update api documentation, but will update if the sphinx
        commands are run in a separate process.
        """
        self._do_mkdocs_things("serve")

    def _do_mkdocs_things(self, cmd: str) -> None:
        root_docs_path = self._devtools_component.find_path("resources/root-docs")
        mkdocs_config = self._devtools_component.find_path("mkdocs.yaml")
        mkdocs_staging_path = self._devtools_component.find_path("dist/docs")
        site_dir_path = self._devtools_component.find_path("dist/site")
        mkdocs_staging_config = self._devtools_component.find_path("dist/mkdocs.yaml")
        # clear any stale state
        self._devtools_component.create_or_empty(mkdocs_staging_path)
        # start with the contents of our root-docs
        self._devtools_component.copy_tree(root_docs_path, mkdocs_staging_path)
        self._devtools_component.symlink(
            # use the README.md at the root as the homepage of the docs site
            self._project_tools.repo_root() / "README.md",
            mkdocs_staging_path / "index.md",
        )
        components = self._project_tools.discover_components()

        for c in components:
            comp_tools = self._project_tools.get_component(c.name)
            docs_path = comp_tools.find_path("docs")
            self._devtools_component.symlink(docs_path, mkdocs_staging_path / c.name)

        # replace the mkdocs config with a fresh version
        mkdocs_staging_config.unlink(missing_ok=True)
        self._devtools_component.copy(mkdocs_config, mkdocs_staging_config)

        args = [
            "--config-file",
            str(mkdocs_staging_config),
        ]
        if cmd == "build":
            args.extend(["--site-dir", str(site_dir_path.resolve())])

        self._devtools_component.run("mkdocs", cmd, *args)

    @cli.command()
    def build_tutorial_notebooks(self) -> None:
        """
        Build the tutorial notebooks section of each component's documentation.

        Converts each *.py jupytext file in the component's docs/_tutorial_notebook_sources
        folder into a markdown notebook in the component's docs/_tutorial_notebooks folder.
        """
        nb_convert_templates_path = self._devtools_component.find_path(
            "resources/nbconvert-templates"
        )
        jupytext_sources_path = self._selected_component.find_path(
            "docs/_tutorial_notebook_sources"
        )
        notebooks_target_path = self._selected_component.find_path("docs/_tutorial_notebooks")
        self._selected_component.create_or_empty(notebooks_target_path)
        source_file_names = [f.stem for f in jupytext_sources_path.glob("*.py")]

        # symlink the jupytext files to the target path
        for file_name in source_file_names:
            logger.warning(f"{file_name} → {notebooks_target_path / f'{file_name}.py'}")
            (notebooks_target_path / f"{file_name}.py").hardlink_to(
                jupytext_sources_path / f"{file_name}.py"
            )

        self._selected_component.run(
            "jupytext",
            "--to",
            "ipynb",
            f"{notebooks_target_path!s}/*.py",
        )
        self._selected_component.run(
            "jupyter",
            "nbconvert",
            f"{notebooks_target_path!s}/*.ipynb",
            "--to",
            "markdown",
            "--execute",
            "--template=mdoutput",
            f"--TemplateExporter.extra_template_basedirs={nb_convert_templates_path}",
        )

        for file_name in source_file_names:
            # delete the .py symlink
            (notebooks_target_path / f"{file_name}.py").unlink()
            # delete the .ipynb file
            (notebooks_target_path / f"{file_name}.ipynb").unlink()
            # add the notebook to the .pages file

        # add a readmd.md file to the target path saying this folder is autogenerated
        source_rel_to_target = "../_tutorial_notebook_sources"
        with (notebooks_target_path / "readme.md").open("w") as f:
            f.write(
                f"This folder is autogenerated from the files in {source_rel_to_target} "
                + "using\n```bash\nrats-devtools.pipx build-tutorial-notebooks\n```\n"
            )
