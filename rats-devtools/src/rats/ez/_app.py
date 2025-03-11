import click

from rats import apps as apps
from rats import cli as cli
from rats import logs as logs
from rats import projects as projects


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        cli.create_group(click.Group("rats-ez"), self).main()

    @cli.command()
    def project_info(self) -> None:
        """Show everything we know about this project."""
        tools = self._tools()
        print(f"repo root: {tools.repo_root().resolve()}")
        print("detected components:")
        for component in tools.discover_components():
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

    @apps.container()
    def _plugins(self) -> apps.Container:
        return projects.PluginContainer(self._app)


def main() -> None:
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
