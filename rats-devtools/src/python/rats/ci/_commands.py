# type: ignore[reportUntypedFunctionDecorator]
import json
import logging
import os
import subprocess
from collections.abc import Iterable

import click

from rats import apps, cli, devtools

logger = logging.getLogger(__name__)


class PluginCommands(cli.CommandContainer):
    _project_tools: devtools.ProjectTools
    _selected_component: devtools.ComponentOperations
    _devtools_component: devtools.ComponentOperations
    _worker_node_runtime: apps.Runtime
    _k8s_runtime: apps.Runtime
    _container_registry: str

    def __init__(
        self,
        project_tools: devtools.ProjectTools,
        selected_component: devtools.ComponentOperations,
        devtools_component: devtools.ComponentOperations,
        worker_node_runtime: apps.Runtime,
        k8s_runtime: apps.Runtime,
        container_registry: str,
    ) -> None:
        self._project_tools = project_tools
        self._selected_component = selected_component
        self._devtools_component = devtools_component
        self._worker_node_runtime = worker_node_runtime
        self._k8s_runtime = k8s_runtime
        self._container_registry = container_registry

    @cli.command(cli.CommandId.auto())
    def install(self) -> None:
        """
        Install the package in the current environment.

        Typically, this just require running `poetry install`. However, some components may run
        additional steps to make the package ready for development. This command does not
        necessarily represent the steps required to install the package in a production
        environments.
        """
        self._selected_component.install()

    @cli.command(cli.CommandId.auto())
    def all_checks(self) -> None:
        """
        Run all the required checks for the component.

        In many cases, if this command completes without error, the CI pipelines in the Pull
        Request should also pass. If the checks for a component run quickly enough, this command
        can be used as a pre-commit hook.
        """
        self._selected_component.pytest()
        self._selected_component.pyright()
        self._selected_component.ruff("format", "--check")
        self._selected_component.ruff("check")

    @cli.command(cli.CommandId.auto())
    @click.argument("files", nargs=-1, type=click.Path(exists=True))
    def fix(self, files: Iterable[str]) -> None:
        """Run any configured auto-formatters for the component."""
        self._selected_component.run("ruff", "format", *files)
        self._selected_component.run("ruff", "check", "--fix", "--unsafe-fixes", *files)

    @cli.command(cli.CommandId.auto())
    def sphinx_apidoc(self) -> None:
        """Build the sphinx apidoc for the package, saving output in dist/sphinx-apidoc."""
        # devtools package has the sphinx config files
        sphinx_resources_path = self._devtools_component.find_path("src/resources/sphinx-docs")
        component_apidoc_path = self._selected_component.find_path("dist/sphinx-apidoc")

        self._selected_component.create_or_empty(component_apidoc_path)
        # we copy the config files from the devtools package into the component we are building.
        self._selected_component.copy_tree(sphinx_resources_path, component_apidoc_path)

        self._selected_component.run(
            "sphinx-apidoc",
            "--doc-project",
            "rats",
            "--tocfile",
            "index",
            "--implicit-namespaces",
            "--module-first",
            "--force",
            "--output-dir",
            str(component_apidoc_path),
            "--templatedir",
            str(component_apidoc_path / "_templates"),
            "src/python/rats",
        )

    @cli.command(cli.CommandId.auto())
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
        gitignore = (api_docs_path / ".gitignore").read_text()
        self._selected_component.create_or_empty(api_docs_path)
        (api_docs_path / ".gitignore").write_text(gitignore)

        self._selected_component.copy_tree(dist_md_path / "markdown", api_docs_path)

    @cli.command(cli.CommandId.auto())
    def mkdocs_build(self) -> None:
        """Build the mkdocs site for every component in the project."""
        self._do_mkdocs_things("build")

    @cli.command(cli.CommandId.auto())
    def mkdocs_serve(self) -> None:
        """
        Serve the mkdocs site for the project and monitor files for changes.

        This command does not automatically update api documentation, but will update if the sphinx
        commands are run in a separate process.
        """
        self._do_mkdocs_things("serve")

    @cli.command(cli.CommandId.auto())  # type: ignore[reportArgumentType]
    @click.argument("version")
    def update_version(self, version: str) -> None:
        """Update the version of the package found in pyproject.toml."""
        self._selected_component.poetry("version", version)

    @cli.command(cli.CommandId.auto())
    def build_wheel(self) -> None:
        """Build a wheel for the package."""
        self._selected_component.poetry("build", "-f", "wheel")

    @cli.command(cli.CommandId.auto())  # type: ignore[reportArgumentType]
    @click.argument("tag")
    def build_image(self, tag: str) -> None:
        """Update the version of the package found in pyproject.toml."""
        file = self._selected_component.find_path("Containerfile")
        if not file.exists():
            raise FileNotFoundError("Containerfile not found in component")

        image_tag = f"{self._container_registry}:{tag}"
        self._selected_component.exe(
            "docker", "build", "-t", image_tag, "--file", str(file), "../"
        )
        if ".azurecr.io/" in self._container_registry:
            acr_registry = self._container_registry.split(".")[0]
            self._selected_component.exe("az", "acr", "login", "--name", acr_registry)
            # for now only pushing automatically if the registry is ACR
            self._selected_component.exe("docker", "push", image_tag)

    @cli.command(cli.CommandId.auto())  # type: ignore[reportArgumentType]
    @click.argument("repository_name")
    def publish_wheel(self, repository_name: str) -> None:
        """
        Publish the wheel to the specified repository.

        This command assumes the caller has the required permissions and the specified repository
        has been configured with poetry.
        """
        self._selected_component.poetry(
            "publish",
            "--repository",
            repository_name,
            "--no-interaction",
            # temporarily skip existing during testing
            "--skip-existing",
        )

    def _do_mkdocs_things(self, cmd: str) -> None:
        root_docs_path = self._devtools_component.find_path("src/resources/root-docs")
        mkdocs_config = self._devtools_component.find_path("mkdocs.yaml")
        mkdocs_staging_path = self._devtools_component.find_path("dist/docs")
        site_dir_path = self._devtools_component.find_path("dist/site")
        mkdocs_staging_config = self._devtools_component.find_path("dist/mkdocs.yaml")
        # clear any stale state
        self._devtools_component.create_or_empty(mkdocs_staging_path)
        # start with the contents of our root-docs
        self._devtools_component.copy_tree(root_docs_path, mkdocs_staging_path)

        # TODO: swap with config in di container
        components = [
            "rats-apps",
            "rats-devtools",
            "rats-pipelines",
            "rats-processors",
            "rats-examples-sklearn",
        ]

        for c in components:
            comp_ops = self._project_tools.get_component(c)
            docs_path = comp_ops.find_path("docs")
            self._devtools_component.symlink(docs_path, mkdocs_staging_path / c)

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

    @cli.command(cli.CommandId.auto())
    def build_tutorial_notebooks(self) -> None:
        """
        Build the tutorial notebooks section of each component's documentation.

        Converts each *.py jupytext file in the component's docs/_tutorial_notebook_sources
        folder into a markdown notebook in the component's docs/_tutorial_notebooks folder.
        """
        nb_convert_templates_path = self._devtools_component.find_path(
            "src/resources/nbconvert-templates"
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

    @cli.command(cli.CommandId.auto())
    @click.option("--exe-id", multiple=True)
    @click.option("--group-id", multiple=True)
    def example_k8s_runtime(self, exe_id: tuple[str, ...], group_id: tuple[str, ...]) -> None:
        if len(exe_id) == 0 and len(group_id) == 0:
            raise ValueError("No executables or groups were passed to the command")

        exes = [apps.ServiceId[apps.Executable](exe) for exe in exe_id]
        groups = [apps.ServiceId[apps.Executable](group) for group in group_id]
        if len(exes):
            self._k8s_runtime.execute(*exes)

        if len(groups):
            self._k8s_runtime.execute_group(*groups)

    @cli.command(cli.CommandId.auto())
    def worker_node(self) -> None:
        """
        Run the worker node process.

        This command is intended to be run in a kubernetes job. It will execute any exes and groups
        that are passed to it by the kubernetes job. Currently, the exes and groups are passed as
        environment variables until a proper mechanism is implemented.
        """
        exes = json.loads(
            os.environ.get("DEVTOOLS_K8S_RUNTIME_EXES", "[]"),
            object_hook=lambda obj: apps.ServiceId[apps.Executable](**obj),
        )
        groups = json.loads(
            os.environ.get("DEVTOOLS_K8S_RUNTIME_GROUPS", "[]"),
            object_hook=lambda obj: apps.ServiceId[apps.Executable](**obj),
        )

        self._worker_node_runtime.execute(*exes)
        self._worker_node_runtime.execute_group(*groups)

    @cli.command(cli.CommandId.auto())
    def image_context_hash(self) -> None:
        """
        Use `git ls-tree` to create a manifest of the files in the image context.

        When building container images, this hash can be used to determine if any of the files in
        the image might have changed.

        Inspired by https://github.com/5monkeys/docker-image-context-hash-action
        """
        containerfile = self._devtools_component.find_path(
            "src/resources/image-context-hash/Containerfile"
        )
        if not containerfile.exists():
            raise FileNotFoundError(
                f"Containerfile not found in devtools component: {containerfile}"
            )

        self._selected_component.exe(
            "docker", "build", "-t", "image-context-hasher", "--file", str(containerfile), "../"
        )
        output = subprocess.run(
            [
                "docker",
                "run",
                "--pull",
                "never",
                "--rm",
                "image-context-hasher",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        lines = sorted(output.strip().split("\n"))

        manifest = self._devtools_component.find_path(".tmp/image-context.manifest")
        hash = self._devtools_component.find_path(".tmp/image-context.hash")
        with manifest.open("w") as f:
            subprocess.run(
                ["git", "ls-tree", "-r", "--full-tree", "HEAD", *lines],
                check=True,
                cwd=self._project_tools.repo_root(),
                stdout=f,
            )

        with hash.open("w") as f:
            subprocess.run(
                ["git", "hash-object", str(manifest)],
                check=True,
                cwd=self._project_tools.repo_root(),
                stdout=f,
            )

        print(
            "warning: if the hash is unexpectedly changing, make sure the below paths are dockerignored"
        )
        print(f"manifest saved: {manifest}")
        print(f"hash saved: {hash}")
        print(f"project hash: {hash.read_text().strip()}")
