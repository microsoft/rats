import logging
import subprocess
import sys
from os import symlink
from pathlib import Path
from shutil import copy, copytree, rmtree

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import cli

logger = logging.getLogger(__name__)


class RatsCiCommands(cli.CommandContainer):
    @cli.command(cli.CommandId.auto())
    def mkdocs_serve(self) -> None:
        """Combine our docs across components and run the mkdocs serve command."""
        self._do_mkdocs_things("serve")

    @cli.command(cli.CommandId.auto())
    def sphinx_build(self) -> None:
        """Build the API documentation for each of the components."""
        self._sphinx_apidoc()
        self._sphinx_markdown()

    @cli.command(cli.CommandId.auto())
    def mkdocs_build(self) -> None:
        """Combine our docs across components using mkdocs build."""
        self._do_mkdocs_things("build")

    @cli.command(cli.CommandId.auto())
    def build_tutorial_notebooks(self) -> None:
        """
        Build the tutorial notebooks section of each component's documentation.

        Converts each *.py jupytext file in the component's docs/_tutorial_notebook_sources
        folder into a markdown notebook in the component's docs/_tutorial_notebooks folder.
        """
        self._build_tutorial_notebooks()

    def _do_mkdocs_things(self, cmd: str) -> None:
        devtools_path = Path("rats-devtools").resolve()
        root_docs_path = devtools_path / "src/resources/root-docs"
        mkdocs_config = devtools_path / "mkdocs.yaml"
        mkdocs_staging_path = devtools_path / "dist/docs"
        site_dir_path = devtools_path / "dist/site"
        mkdocs_staging_config = devtools_path / "dist/mkdocs.yaml"
        # clear any stale state
        rmtree(mkdocs_staging_path, ignore_errors=True)

        # start with the contents of our root-docs
        copytree(root_docs_path, mkdocs_staging_path)

        components = [
            "rats-apps",
            "rats-devtools",
            "rats-pipelines",
            "rats-processors",
        ]

        for c in components:
            component_docs_path = Path(c).resolve() / "docs"
            symlink(component_docs_path, mkdocs_staging_path / c)

        # replace the mkdocs config with a fresh version
        mkdocs_staging_config.unlink(missing_ok=True)
        copy(mkdocs_config, mkdocs_staging_config)

        args = [
            "--config-file",
            str(mkdocs_staging_config),
        ]
        if cmd == "build":
            args.extend(["--site-dir", str(site_dir_path.resolve())])

        try:
            subprocess.run(
                [
                    "poetry",
                    "run",
                    "mkdocs",
                    cmd,
                    *args,
                ],
                cwd=devtools_path,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _sphinx_apidoc(self) -> None:
        components = [
            "rats-apps",
            "rats-devtools",
            "rats-pipelines",
            "rats-processors",
        ]
        sphinx_resources_path = Path("rats-devtools/src/resources/sphinx-docs").resolve()

        for c in components:
            apidoc_path = Path(f"{c}/dist/sphinx-apidoc").resolve()
            rmtree(apidoc_path, ignore_errors=True)
            copytree(sphinx_resources_path, apidoc_path)

            sphinx_command = [
                "poetry",
                "run",
                "sphinx-apidoc",
                "--doc-project",
                "rats",
                "--tocfile",
                "index",
                "--implicit-namespaces",
                "--module-first",
                "--force",
                "--output-dir",
                str(apidoc_path),
                "--templatedir",
                str(apidoc_path / "_templates"),
                "src/python/rats",
            ]
            try:
                subprocess.run(sphinx_command, cwd=c, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

    def _sphinx_markdown(self) -> None:
        components = [
            "rats-apps",
            "rats-devtools",
            "rats-pipelines",
            "rats-processors",
        ]

        for c in components:
            rmtree(f"{c}/dist/sphinx-markdown", ignore_errors=True)
            sphinx_command = [
                "poetry",
                "run",
                "sphinx-build",
                "-M",
                "markdown",
                "dist/sphinx-apidoc",
                "dist/sphinx-markdown",
            ]
            try:
                subprocess.run(sphinx_command, cwd=c, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

            copytree(
                f"{c}/dist/sphinx-markdown/markdown",
                f"{c}/docs/api",
                dirs_exist_ok=True,
            )

    def _build_tutorial_notebooks(self) -> None:
        """
        Build the tutorial notebooks section of each component's documentation.

        Converts each *.py jupytext file in the component's docs/_tutorial_notebook_sources
        folder into a markdown notebook in the component's docs/_tutorial_notebooks folder.
        """
        components = [
            # "rats-apps",
            # "rats-devtools",
            # "rats-pipelines",
            "rats-processors",
            "rats-examples-sklearn",
        ]
        nb_convert_templates_path = Path(
            "rats-devtools/src/resources/nbconvert-templates"
        ).resolve()

        commands = [
            "poetry run jupytext --to ipynb *.py".split(),
            f"poetry run jupyter nbconvert *.ipynb --to markdown --execute --template=mdoutput --TemplateExporter.extra_template_basedirs={nb_convert_templates_path}".split(),
        ]

        for c in components:
            logger.info("Building notebooks for %s", c)
            jupytext_sources_path = Path(f"{c}/docs/_tutorial_notebook_sources").resolve()
            notebooks_target_path = Path(f"{c}/docs/_tutorial_notebooks").resolve()
            rmtree(notebooks_target_path, ignore_errors=True)
            notebooks_target_path.mkdir(parents=True, exist_ok=True)
            source_file_names = [f.stem for f in jupytext_sources_path.glob("*.py")]

            # symlink the jupytext files to the target path
            for file_name in source_file_names:
                (jupytext_sources_path / f"{file_name}.py").hardlink_to(
                    notebooks_target_path / f"{file_name}.py"
                )

            for cmd in commands:
                try:
                    subprocess.run(cmd, cwd=notebooks_target_path, check=True)
                except subprocess.CalledProcessError as e:
                    sys.exit(e.returncode)

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
