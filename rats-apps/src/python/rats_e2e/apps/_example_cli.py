from textwrap import dedent
from uuid import uuid4

import click

from rats import apps, cli, logs

from ._example_inputs import InputExampleApp
from ._example_minimal import MinimalExampleApp
from ._services import ExampleAppServices


class ExampleContextContainer(apps.Container, apps.PluginMixin):
    """
    Our test context container provides the input data to our applications.

    We'll pass this container into the different example applications, so the developer of a given
    application can the services defined in here as being part of their parent container often
    defined as `self._app`.
    """

    @apps.service(ExampleAppServices.INPUT)
    def _input(self) -> str:
        """
        A random value we want to be made available to our example apps.

        Because the `apps.Container` service providers are cached, our `uuid` will be static for
        each instance of this container
        """
        return str(uuid4())


class ExampleCliApp(apps.AppContainer, cli.Container, apps.PluginMixin):
    """Test application that exposes a few example uses of `rats.apps`."""

    def execute(self) -> None:
        """Register our cli commands and run them using click."""
        apps.run(apps.AppBundle(app_plugin=logs.ConfigureApplication))
        cli.create_group(click.Group("rats_e2e.apps"), self)()

    @cli.command()
    def _run_all(self) -> None:
        """Run examples using `apps.AppBundle()`."""
        app_plugins = [
            MinimalExampleApp,
            InputExampleApp,
        ]

        print("running the following applications using the `apps.AppBundle` class:")
        for cls in app_plugins:
            print(f"  - {cls.__module__}:{cls.__name__}")

        print("\nfirst running apps without any injected context")
        print("=" * 20)

        apps.run_plugin(*app_plugins)

        print("=" * 20)

        print(
            dedent(f"""
            running with external context container: {ExampleContextContainer}
            when we specify the context using the `container_plugin` argument, each application
            will receive a new instance of the context built by the `AppBundle` class.
            """)
        )
        print("=" * 20)

        for cls in app_plugins:
            apps.run(apps.AppBundle(app_plugin=cls, container_plugin=ExampleContextContainer))

        print("=" * 20)
        print(
            dedent(f"""
            running with shared external context container: {ExampleContextContainer}
            when we specify the context using the `context` argument, each application can be
            given the same instance.
            """)
        )
        print("=" * 20)

        ctx = ExampleContextContainer(apps.CompositeContainer())
        for cls in app_plugins:
            apps.run(apps.AppBundle(app_plugin=cls, context=ctx))
