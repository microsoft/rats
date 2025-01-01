import click

from rats import apps as apps
from rats import cli as cli
from rats import logs as logs
from rats import projects as projects


@apps.autoscope
class AppServices:
    ON_REGISTER = apps.ServiceId[apps.Executable]("on-register")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")

    HELLO_WORLD_EXE = apps.ServiceId[apps.Executable]("hello-world-exe")


class Application(apps.AppContainer, apps.PluginMixin, cli.Container):
    def execute(self) -> None:
        runtime = apps.StandardRuntime(self._app)
        runtime.execute_group(AppServices.ON_REGISTER)
        self._app.get(AppServices.MAIN_CLICK)()

    @cli.command()
    def project_info(self) -> None:
        """Show everything we know about this project."""
        tools = self._tools()
        print(f"repo root: {tools.repo_root().resolve()}")
        print("detected components:")
        for component in tools.discover_components():
            if component == tools.devtools_component():
                print(f"🛠 {component.name}")
            else:
                print(f"   {component.name}")

    @cli.command()
    def project_hash(self) -> None:
        """Calculate the hash of the project manifest."""
        print(self._tools().image_context_hash())

    @cli.command()
    def project_manifest(self) -> None:
        """Show the project manifest."""
        print(self._tools().image_context_manifest())

    def _tools(self) -> projects.ProjectTools:
        return self._app.get(projects.PluginServices.PROJECT_TOOLS)

    @apps.service(AppServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        return cli.create_group(
            click.Group("rats-devtools", help="develop your ideas with ease"),
            self,
        )

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            apps.PluginContainers(self, "rats.apps.plugins"),
            apps.PluginContainers(self, "rats.devtools.plugins"),
        )

    @apps.service(AppServices.HELLO_WORLD_EXE)
    def _hello_world(self) -> apps.Executable:
        return apps.App(lambda: print("hello, world"))


def run() -> None:
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
