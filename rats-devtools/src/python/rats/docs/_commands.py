import subprocess
import sys
from os import symlink
from pathlib import Path
from shutil import copy, copytree, rmtree

import click

from rats import apps

from ._ids import PluginServices


class RatsCiCommands(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.GROUPS.command("mkdocs-serve"))
    def mkdocs_serve_command(self) -> click.Command:
        @click.command
        def mkdocs_serve() -> None:
            """Combine our docs across components and run the mkdocs serve command."""
            self._do_mkdocs_things("serve")

        return mkdocs_serve

    @apps.service(PluginServices.GROUPS.command("sphinx-build"))
    def sphinx_build_command(self) -> click.Command:
        @click.command()
        def sphinx_build() -> None:
            """Build the API documentation for each of the components."""
            self._sphinx_apidoc()
            self._sphinx_markdown()

        return sphinx_build

    @apps.service(PluginServices.GROUPS.command("mkdocs-build"))
    def mkdocs_build_command(self) -> click.Command:
        @click.command
        def mkdocs_build() -> None:
            """Combine our docs across components using mkdocs build."""
            self._do_mkdocs_things("build")

        return mkdocs_build

    @apps.service(PluginServices.GROUPS.command("build-jupytext-notebooks"))
    def build_jupytext_notebooks_command(self) -> click.Command:
        @click.command()
        def build_jupytext_notebooks() -> None:
            """
            Build the notebooks section of each component's documentation.

            Converts each *.py jupytext file in the components docs/_jupytext_tutorials directory into
            a markdown notebook.
            """
            components = [
                # "rats-apps",
                # "rats-devtools",
                # "rats-pipelines",
                "rats-processors",
            ]
            nb_convert_templates_path = Path(
                "rats-devtools/src/resources/nbconvert-templates"
            ).resolve()

            commands = [
                "poetry run jupytext --to ipynb *.py".split(),
                f"poetry run jupyter nbconvert *.ipynb --to markdown --execute --template=mdoutput --TemplateExporter.extra_template_basedirs={nb_convert_templates_path}".split(),
            ]

            def find_jupytext_files(path: Path) -> list[tuple[str, str]]:
                def file_name_to_order_and_title(file_name: str) -> tuple[int, str, str]:
                    tokens = file_name.split("_")
                    try:
                        order = int(tokens[0])
                    except ValueError:
                        raise ValueError(
                            f"Expected the names files under {path} to start with an "
                            + "integer.  Found file {file_name}.py."
                        ) from None
                    title = " ".join(tokens[1:]).capitalize()
                    return order, file_name, title

                files = sorted(
                    [file_name_to_order_and_title(f.stem) for f in path.glob("*.py")],
                    key=lambda x: x[0],
                )
                return [(f[1], f[2]) for f in files]

            for c in components:
                jupytext_sources_path = Path(f"{c}/docs/_jupytext_tutorials").resolve()
                notebooks_target_path = Path(f"{c}/docs/notebooks").resolve()
                rmtree(notebooks_target_path, ignore_errors=True)
                notebooks_target_path.mkdir(parents=True, exist_ok=True)
                jupytext_files = find_jupytext_files(jupytext_sources_path)

                # symlink the jupytext files to the target path
                for n, _ in jupytext_files:
                    (jupytext_sources_path / f"{n}.py").link_to(notebooks_target_path / f"{n}.py")

                for cmd in commands:
                    try:
                        subprocess.run(cmd, cwd=notebooks_target_path, check=True)
                    except subprocess.CalledProcessError as e:
                        sys.exit(e.returncode)

                dotpages_lines = ["nav:"]
                for n, title in jupytext_files:
                    # delete the .py symlink
                    (notebooks_target_path / f"{n}.py").unlink()
                    # delete the .ipynb file
                    (notebooks_target_path / f"{n}.ipynb").unlink()
                    # add the notebook to the .pages file
                    dotpages_lines.append(f"  - {title}: {n}.md")

                # update the .pages file
                dotpages_path = notebooks_target_path / ".pages"
                dotpages_path.write_text("\n".join(dotpages_lines))

        return build_jupytext_notebooks

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
