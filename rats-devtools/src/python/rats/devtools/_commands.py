import logging
import subprocess
import sys
from os import symlink
from pathlib import Path
from shutil import copy, copytree, rmtree

import click

from ._click import ClickCommandRegistry, command

logger = logging.getLogger(__name__)


class RatsDevtoolsCommands(ClickCommandRegistry):
    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def install(self, component_path: str) -> None:
        """Build the documentation site for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(["poetry", "install"], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    def build_api_docs(self) -> None:
        """Build the API documentation for each of the components."""
        self._sphinx_apidoc()
        self._sphinx_markdown()

    def _sphinx_apidoc(self) -> None:
        components = [
            # "rats-apps",
            "rats-devtools",
            "rats-pipelines",
            "rats-processors",
        ]

        for c in components:
            apidoc_path = Path(f"{c}/dist/sphinx-apidoc").resolve()
            sphinx_resources_path = Path("rats-devtools/src/resources/sphinx-docs").resolve()
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
            # "rats-apps",
            "rats-devtools",
            "rats-pipelines",
            "rats-processors",
            "rats-examples-sklearn",
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

    @command
    def build_jupytext_notebooks(self) -> None:
        """Build the notebooks section of each component's documentation.

        Converts each *.py jupytext file in the components docs/_jupytext_tutorials directory into
        a markdown notebook.
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
            jupytext_sources_path = Path(f"{c}/docs/_jupytext_tutorials").resolve()
            notebooks_target_path = Path(f"{c}/docs/notebooks").resolve()
            rmtree(notebooks_target_path, ignore_errors=True)
            notebooks_target_path.mkdir(parents=True, exist_ok=True)
            source_file_names = [f.stem for f in jupytext_sources_path.glob("*.py")]

            # symlink the jupytext files to the target path
            for file_name in source_file_names:
                (jupytext_sources_path / f"{file_name}.py").link_to(
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

    @command
    def mkdocs_serve(self) -> None:
        """Combine our docs across components and run the mkdocs serve command."""
        self._do_mkdocs_things("serve")

    @command
    def mkdocs_build(self) -> None:
        """Combine our docs across components using mkdocs build."""
        self._do_mkdocs_things("build")

    def _copy_notebooks_from_component(self, mkdocs_staging_path: Path, component: str) -> None:
        source_path = mkdocs_staging_path / component / "notebooks"
        target_path = mkdocs_staging_path / "tutorial_notebooks"
        if (source_path).exists():
            for file_path in (source_path).glob("*"):
                symlink(file_path, target_path / file_path.name)

    def _create_notebook_nav_page(self, mkdocs_staging_path: Path) -> None:
        notebooks_path = mkdocs_staging_path / "tutorial_notebooks"

        def file_name_to_order_and_title(file_name: str) -> tuple[int, str, str]:
            tokens = file_name.split("_")
            try:
                order = int(tokens[0])
            except ValueError:
                raise ValueError(
                    f"Expected the names files under {notebooks_path} to start with an "
                    + "integer.  Found file {file_name}.md."
                ) from None
            title = " ".join(tokens[1:]).capitalize()
            return order, file_name, title

        notebooks = sorted(
            [file_name_to_order_and_title(p.stem) for p in notebooks_path.glob("*.md")],
            key=lambda t: t[0],
        )
        dotpages_lines = ["nav:"]
        for _, file_name, title in notebooks:
            dotpages_lines.append(f"  - {title}: {file_name}.md")
            # update the .pages file
        dotpages_path = notebooks_path / ".pages"
        dotpages_path.write_text("\n".join(dotpages_lines))

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
            "rats-examples-sklearn",
        ]

        for c in components:
            component_docs_path = Path(c).resolve() / "docs"
            symlink(component_docs_path, mkdocs_staging_path / c)
            self._copy_notebooks_from_component(mkdocs_staging_path, c)

        self._create_notebook_nav_page(mkdocs_staging_path)

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

    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def build_docs(self, component_path: str) -> None:
        """Build the documentation site for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"
        site_dir_path = p / "dist/site"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(
                [
                    "poetry",
                    "run",
                    "mkdocs",
                    "build",
                    "--site-dir",
                    str(site_dir_path.resolve()),
                ],
                cwd=component_path,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def build_wheel(self, component_path: str) -> None:
        """Build the python wheel for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(["poetry", "build", "-f", "wheel"], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    @click.argument("repository_name", type=str)
    def publish_wheel(self, component_path: str, repository_name: str) -> None:
        """Publish the python wheel for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(
                [
                    "poetry",
                    "publish",
                    "--repository",
                    repository_name,
                    "--no-interaction",
                    # temporarily skip existing during testing
                    "--skip-existing",
                ],
                cwd=component_path,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def test(self, component_path: str) -> None:
        """Build the python wheel for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(["poetry", "run", "pytest"], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    def ping(self) -> None:
        """No-op used for testing."""
        print("pong")
