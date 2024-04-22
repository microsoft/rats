import subprocess
import sys
from os import symlink
from pathlib import Path
from shutil import copy, copytree, rmtree

import click

from ._click import ClickCommandRegistry, command


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

    @command
    def mkdocs_serve(self) -> None:
        """Combine our docs across components and run the mkdocs serve command."""
        self._do_mkdocs_things("serve")

    @command
    def mkdocs_build(self) -> None:
        """Combine our docs across components using mkdocs build."""
        self._do_mkdocs_things("build")

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
