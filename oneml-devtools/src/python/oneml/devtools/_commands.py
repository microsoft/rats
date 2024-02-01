from shutil import copy, copytree, rmtree

from tempfile import mkdtemp

import json
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from os import symlink

import click
import toml

from oneml.services import IExecutable, ServiceProvider

from ._click import ClickCommandRegistry, command


class OnemlDevtoolsCli(IExecutable):

    _registries_group_provider: ServiceProvider[Iterable[ClickCommandRegistry]]

    def __init__(self, registries_group_provider: ServiceProvider[Iterable[ClickCommandRegistry]]) -> None:
        self._registries_group_provider = registries_group_provider

    def execute(self) -> None:
        cli = click.Group()
        for registry in self._registries_group_provider():
            registry.register(cli)

        cli()


class OnemlDevtoolsCommands(ClickCommandRegistry):

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
    def build_sphinx_docs(self) -> None:
        self._sphinx_apidoc()
        self._sphinx_markdown()

    def _sphinx_apidoc(self) -> None:
        components = [
            "oneml-adocli",
            "oneml-devtools",
            "oneml-pipelines",
            "oneml-processors",
        ]

        for c in components:
            apidoc_path = Path(f"{c}/dist/sphinx-apidoc").resolve()
            sphinx_config = Path("oneml-devtools/src/resources/sphinx-docs/conf.py").resolve()
            rmtree(apidoc_path, ignore_errors=True)

            sphinx_command = [
                "poetry", "run",
                "sphinx-apidoc",
                "--doc-project",
                "oneml",
                "--tocfile",
                "index",
                "--implicit-namespaces",
                "--module-first",
                "--force",
                "--output-dir",
                str(apidoc_path),
                f"src/python/oneml",
            ]
            try:
                subprocess.run(sphinx_command, cwd=c, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

            copy(sphinx_config, apidoc_path / "conf.py")

    def _sphinx_markdown(self) -> None:
        components = [
            "oneml-adocli",
            "oneml-devtools",
            "oneml-pipelines",
            "oneml-processors",
        ]

        for c in components:
            rmtree(f"{c}/dist/sphinx-markdown", ignore_errors=True)
            sphinx_command = [
                "poetry", "run",
                "sphinx-build",
                "-M", "markdown",
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
    def serve_gh_pages(self) -> None:
        """Run `build-gh-pages` and then serve the files to view the results locally."""

        self._do_mkdocs_things("serve")

    @command
    def build_gh_pages(self) -> None:
        """Combine all documentation and build the full gh-pages site."""

        self._do_mkdocs_things("build")

    def _do_mkdocs_things(self, cmd: str) -> None:
        devtools_path = Path("oneml-devtools").resolve()
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
            "oneml-adocli",
            "oneml-devtools",
            "oneml-pipelines",
            "oneml-processors",
        ]

        for c in components:
            component_docs_path = Path(c).resolve() / "docs"
            symlink(component_docs_path, mkdocs_staging_path / c)

        # for some reason, mkdocs does not like symlinks for the main config file
        if mkdocs_staging_config.exists():
            mkdocs_staging_config.unlink()

        # replace it with a fresh version of the config
        copy(mkdocs_config, mkdocs_staging_config)

        args = [
            "--config-file", str(mkdocs_staging_config),
        ]
        if cmd == "build":
            args.extend(["--site-dir", str(site_dir_path.resolve())])

        try:
            subprocess.run([
                "poetry", "run",
                "mkdocs", cmd,
                *args,
            ], cwd=devtools_path, check=True)
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
            subprocess.run([
                "poetry", "run",
                "mkdocs", "build",
                "--site-dir", str(site_dir_path.resolve()),
            ], cwd=component_path, check=True)
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
            subprocess.run([
                "poetry", "publish",
                "--repository", repository_name,
                "--no-interaction",
                # temporarily skip existing during testing
                "--skip-existing",
            ], cwd=component_path, check=True)
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
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def generate_cg_manifest(self, component_path: str) -> None:
        """Build the component governance file for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"
        lock_path = p / "poetry.lock"

        if not p.is_dir() or not pyproject_path.is_file() or not lock_path.is_file():
            raise ValueError(f"invalid component path: {component_path}")

        poetry_lockfile = toml.load(lock_path)
        manifest_path = p / "cgmanifest.json"

        manifest_path.write_text(
            json.dumps(
                {
                    "Registrations": [
                        {
                            "Component": {
                                "Type": "pip",
                                "pip": {
                                    "Name": package["name"],
                                    "Version": package["version"],
                                },
                            },
                            "DevelopmentDependency": False,
                        }
                        for package in poetry_lockfile["package"]
                        if package["source"]["type"] != "directory"
                    ]
                },
                indent=4,
            )
        )

    @command
    def ping(self) -> None:
        """No-op used for testing."""
        print("pong")
