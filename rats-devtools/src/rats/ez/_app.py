import click

from rats import apps as apps
from rats import cli as cli
from rats import logs as logs
from rats import projects as projects


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    """
    Main application for the `rats-ez` cli commands.

    Not typically used directly, but can be invoked using [rats.apps.AppBundle][] within tests or
    in advanced workflows.

    ```python
    from rats import apps, ez


    ez_app = apps.AppBundle(app_plugin=ez.Application)
    ez_app.project_hash()
    ez_app.project_info()
    ez_app.project_manifest()
    ez_app.run(("poetry", "update"))
    ```

    !!! warning
        Calling `ez_app.execute()` is unlikely to behave as expected, because [sys.argv][] is
        parsed by the [click][] library.
    """

    def execute(self) -> None:
        """Parses [sys.argv][] to run the `rats-ez` cli application."""
        cli.create_group(click.Group("rats-ez"), self).main()

    @cli.command()
    def project_info(self) -> None:
        """
        Show basic project structure information.

        ```
        $ rats-ez project-info
        repo root: /…/rats
        detected components:
           rats-devtools
           rats-apps
           rats
        ```
        """
        tools = self._tools()
        print(f"repo root: {tools.repo_root().resolve()}")
        print("detected components:")
        for component in tools.discover_components():
            print(f"   {component.name}")

    @cli.command()
    def project_hash(self) -> None:
        """
        Calculate the hash of the project manifest.

        The hash is calculated with [rats.projects.ProjectTools.image_context_hash][]

        ```
        $ rats-ez project-hash
        705696aadf70c3d78b230ea029658f9e9b5ee1d4ecd3f1485725d36184f1e816
        ```
        """
        print(self._tools().image_context_hash())

    @cli.command()
    def project_manifest(self) -> None:
        """
        Show the project manifest.

        The manifest is taken from [rats.projects.ProjectTools.image_context_manifest][]

        ```
        $ rats-ez project-manifest
        …
        f604f…daeadd        .devcontainer/devcontainer.json
        cd384…40b228        .devcontainer/direnvrc
        61fa9…64db82        .devcontainer/on-create.sh
        99ee7…aa6661        .devcontainer/post-create.sh
        8ef70…387510        .dockerignore
        …
        96928…93f240        rats-apps/poetry.lock
        aa057…0deabb        rats-apps/poetry.toml
        2c905…9c31b1        rats-apps/pyproject.toml
        626c9…fe8e75        rats-apps/src/rats/annotations/__init__.py
        be5cd…5c06f2        rats-apps/src/rats/annotations/__main__.py
        5241e…889437        rats-apps/src/rats/annotations/_functions.py
        …
        01a05…d1fc56        rats-devtools/mkdocs.yaml
        8833e…890b76        rats-devtools/poetry.lock
        aa057…0deabb        rats-devtools/poetry.toml
        d346c…3ec564        rats-devtools/pyproject.toml
        cf568…47c48c        rats-devtools/src/rats/aml/__init__.py
        d22fa…b0f5bf        rats-devtools/src/rats/aml/__main__.py
        69445…d8092d        rats-devtools/src/rats/aml/_app.py
        2d9a1…3d444a        rats-devtools/src/rats/aml/_configs.py
        b2d7d…8f1444        rats-devtools/src/rats/aml/_request.py
        …
        ```
        """
        print(self._tools().image_context_manifest())

    @cli.command()
    @click.argument("cmd")
    @click.argument("args", nargs=-1)
    @click.option(
        "--component",
        "-c",
        multiple=True,
        help="limit the commands to a set of provided component names",
    )
    def run(self, cmd: str, args: tuple[str, ...], component: tuple[str, ...]) -> None:
        r"""
        Run a command in all of the components in your project.

        By default, the command runs in all components; but one or more `--component` options can
        be provided to limit the commands to a set of components.

        ```
        $ rats-ez run which python
        running command: (which python) on ['rats-devtools', 'rats-apps', 'rats']
        /…/rats/rats-devtools/.venv/bin/python
        /…/rats/rats-apps/.venv/bin/python
        /…/rats/rats/.venv/bin/python
        ```

        Args:
            cmd: the name of the command or full path if not present in `$PATH`
            args: zero or more arguments passed to the command
            component: filters the command to only run in the provided components
        """
        available = self._tools().discover_components()
        selected = [projects.ComponentId(name) for name in component] if component else available
        for s in selected:
            if s not in available:
                raise ValueError(f"invalid component specified: {s.name}")

        names = [s.name for s in selected]

        print(f"running command: ({cmd} {' '.join(args)}) on {names}")
        for c in selected:
            component_tools = self._tools().get_component(c.name)
            component_tools.run(cmd, *args)

    def _tools(self) -> projects.ProjectTools:
        return self._app.get(projects.PluginServices.PROJECT_TOOLS)

    @apps.container()
    def _plugins(self) -> apps.Container:
        return projects.PluginContainer(self._app)


def main() -> None:
    """The main entry-point for the application, used to define the python script for `rats-ez."""
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
