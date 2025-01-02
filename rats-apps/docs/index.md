---
title: Introduction
---

The `rats-apps` package helps create applications; a small set of modules that eliminate the most
common boilerplate code when creating applications of any kind. We do this mainly by providing a
set of libraries to define service containers, and using the service containers to hide the
complexity of creating services–like authentication, storage, or database clients–from other parts
of the system, allowing developers to focus on the business logic of the application. Often refered
to as [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection), we use our
service containers to separate the concerns of constructing objects and using them.

## Installation

Use `pip` or your favorite packaging tool to install the package from PyPI.

```bash
pip install rats-apps
```

## What is an application?

Let's start with a standard python script, and slowly migrate it to be a rats application in order
to explain a few main details. Creating a `__main__.py` file in a package makes it executable.
After the common python boilerplate code is added, this is typically what we find in the wild:

=== ":material-language-python: ~/code/src/foo/\_\_main\_\_.py"
    ```python
    def main() -> None:
        print("hello, world")


    if __name__ == "__main__":
        main()
    ```

=== ":material-console: ~/code"
    ```bash
    python -m foo
    ```

Using this pattern, we can define our application with a small modification, turning our `main()`
function into a runnable rats application, and then running it:

=== ":material-language-python: ~/code/src/foo/\_\_main\_\_.py"
    ```python
    from rats import apps


    def main() -> None:
        print("hello, world")


    if __name__ == "__main__":
        apps.run(apps.App(main))
    ```

!!! info
    The [rats.apps.App][] class is used to quickly turn a script entry point–`Callable[[], None]`
    –into an object with an `execute()` method, defined by our [rats.apps.Executable][]
    interface.

## Application Containers & Plugins

We can start to leverage [rats.apps][] to make our application easy to extend. Let's replace our use
of the [rats.apps.App][] wrapper and move our `main()` function into a class. Using the
[rats.apps.AppContainer][] and [rats.apps.PluginMixin][] classes, we finish adapting our example
to be a rats application.

=== ":material-language-python: ~/code/src/foo/\_\_main\_\_.py"

    ```python
        from rats import apps


        class Application(apps.AppContainer, apps.PluginMixin):
            def execute() -> None:
                print("hello, world")


        if __name__ == "__main__":
            apps.run_plugin(Application)
    ```

!!! info
    If you're making these changes to an existing code base, you should be able to run things to
    validate that everything still works as it did before. Your `main()` function is now in
    the `execute()` method of your new `Application` class, but none of the behavior of your
    application should have been affected.

Now that we have a fully defined rats application; we can use [rats.apps.Container][] instances to
make services available to our application while remaining decoupled from the details of how these
services are initialized. A common use case for this is to give our team access to the azure
storage clients without needing to specify the authentication details; allowing us to ensure our
application is functional in many compute environments.

=== ":material-language-python: ~/code/src/foo/\_\_init\_\_.py"

    ```python
        from ._plugin import PluginContainer

        __all__ = ["PluginContainer"]
    ```

=== ":material-language-python: ~/code/src/foo/\_\_main\_\_.py"

    ```python
        from rats import apps
        import foo


        class Application(apps.AppContainer, apps.PluginMixin):

            def execute() -> None:
                blob_client = self._app.get(foo.BLOB_SERVICE_ID)
                print(f"hello, world. loaded blob client: {blob_client}")

            @apps.container()
            def _plugins(self) -> apps.Container:
                return foo.PluginContainer(self._app)


        if __name__ == "__main__":
            apps.run_plugin(Application)
    ```

=== ":material-language-python: ~/code/src/foo/_plugin.py"

    ```python
        from rats import apps
        from azure.storage.blob import BlobServiceClient

        BLOB_SERVICE_ID = apps.ServiceId[BlobServiceClient]("blob-client")


        class PluginContainer(apps.Container, apps.PluginMixin):

            @apps.service(BLOB_SERVICE_ID)
            def _blob_client(self) -> BlobServiceClient:
                credential = DefaultAzureCredential()
                return BlobServiceClient(
                    account_url=f"https://example.blob.core.windows.net/",
                    credential=credential,
                )
    ```

!!! success
    Following these patterns, we can make services available to others with plugin containers; and
    we can combine these containers to create applications. The [rats.apps][] module has additional
    libraries to help define different types of applications, designed to help your solutions
    evolve as ideas mature. Our first runnable example was a single instance of the
    [apps.AppContainer][] interface with an `execute()` method; but a larger project might have
    a few modules providing different aspects of the application's needs by sharing a set of
    service ids and a plugin container.

## Installable Plugins

We use the standard [Entry Points](https://packaging.python.org/en/latest/specifications/entry-points/)
mechanism to allow authors to make their application extensible. These plugins are instances of
[apps.Container][] and loaded into applications like our previous examples.

=== ":material-file-settings: ~/code/pyproject.toml"
    ```toml
    [tool.poetry.plugins."foo.plugins"]
    "foo" = "foo:PluginContainer"
    ```

=== ":material-language-python: ~/code/src/foo/\_\_main\_\_.py"
    ```python
        from rats import apps
        import foo


        class Application(apps.AppContainer, apps.PluginMixin):

            def execute() -> None:
                blob_client = self._app.get(foo.BLOB_SERVICE_ID)
                print(f"hello, world. loaded blob client: {blob_client}")

            @apps.container()
            def _plugins(self) -> apps.Container:
                return apps.PluginContainers("foo.plugins")


        if __name__ == "__main__":
            apps.run_plugin(Application)
    ```

!!! success
    We used [rats.app] to define an application, and used a service provided by a plugin container
    that is loaded through a python entry point. You can create a script entry in your
    `pyproject.toml` file to expose your application through a terminal command:

    === ":material-language-python: ~/code/src/foo/\_\_init\_\_.py"
        ```python
            from ._app import Application, main
            from ._plugin import PluginContainer


            __all__ = [
                "Application",
                "main",
                "PluginContainer",
            ]
        ```
    === ":material-file-settings: ~/code/pyproject.toml"
        ```toml
            [tool.poetry.plugins."foo.plugins"]
            "foo" = "foo:PluginContainer"

            [tool.poetry.scripts]
            foo = "foo:main"
        ```
