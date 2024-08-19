title: intro
---
## rats-apps

The `rats-apps` package helps create applications; a small set of modules that eliminate the most 
common boilerplate code when creating applications of any kind. Install it with `pip install 
rats-apps`!

### What is an application?
Creating a `__main__.py` file in a package makes it easily executable. After the common python
boilerplate code is added, this is typically what we find in the wild:

=== ":material-language-python: ~/code/src/python/foo/__main__.py"
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

Using this pattern, we can define our application with a small modification:

=== ":material-language-python: ~/code/src/python/foo/__main__.py"
    ```python
    from rats import apps


    def main() -> None:
        print("hello, world")


    if __name__ == "__main__":
        app = apps.SimpleApplication()
        app.execute_callable(main)
    ```

### Application Containers & Plugins

We can start to leverage `rats.apps` to make our application easy to extend. We use the
standard [Entry  Points](https://packaging.python.org/en/latest/specifications/entry-points/)
mechanism, pick a name for our group, and enable it in our `apps.SimpleApplication` instance.

=== ":material-file-settings: ~/code/pyproject.toml"
    ```toml
    [tool.poetry.plugins."foo.plugins"]
    "foo" = "foo:PluginContainer"
    ```

=== ":material-language-python: ~/code/src/python/foo/__main__.py"
    ```python
    from rats import apps


    def main() -> None:
        print("hello, world")


    if __name__ == "__main__":
        app = apps.SimpleApplication("foo.plugins")
        app.execute_callable(main)
    ```

With our newly created plugin group, `foo.plugins`, we use `apps.Container` classes to extend
the functionality of the application. We've already registered `foo.PluginContainer` in the
`pyproject.toml` file, so let's create the class and refresh our virtual environment.

=== ":material-language-python: ~/code/src/python/foo/_plugin.py"
    ```python
    from rats import apps


    class PluginContainer(apps.Container):

        _app: apps.Container

        def __init__(self, app: apps.Container) -> None:
            self._app = app
    ```

=== ":material-language-python: ~/code/src/python/foo/__init__.py"
    ```python
    from ._plugin import PluginContainer

    __all__ = [
        "PluginContainer",
    ]
    ```

=== ":material-console: ~/code"
    ```bash
    poetry install
    python -m foo
    ```

!!! tip
    Any number of plugins can be registered this way. Extending the behavior of our
    applications through plugins allows us to provide an opinionated, extensive default
    experience, but allow advanced, unplanned uses to adjust most implementation details. The
    `rats` project has a few built-in plugins for common application capabilities that we can
    explore more later.

Our plugin class is an implementation of the `apps.Container` protocol, which allows us to
quickly make services available to other parts of the system. Let's finish moving our `main()`
function into our plugin container and use `apps.SimpleApplication` to run it.

=== ":material-language-python: ~/code/src/python/foo/_plugin.py"
    ```python
    from tempfile import mkdtemp
    from rats import apps


    @apps.autoscope
    class PluginServices:
        MAIN = ServiceId[apps.Executable]("main")
        FOO_PATH = ServiceId[Path]("foo-path")


    class PluginContainer(apps.Container):

        _app: apps.Container

        def __init__(self, app: apps.Container) -> None:
            self._app = app

        @apps.service(PluginServices.MAIN)
        def _main(self) -> apps.Executable:
            def main() -> None:
                print("hello, world")
                # we can access any service defined in a loaded plugin container.
                print(f"foo path: {self._app.get(PluginServices.FOO_PATH)}")

            return apps.App(main)

        @apps.service(PluginServices.FOO_PATH)
        def _foo_path(self) -> Path:
            return Path(mkdtemp(dir=Path(".tmp")))
    ```

=== ":material-language-python: ~/code/src/python/foo/\_\_main\_\_.py"
    ```python
    from rats import apps
    from ._plugin import PluginServices


    def run() -> None:
        app = apps.SimpleApplication("foo.plugins")
        app.execute(PluginServices.MAIN)


    if __name__ == "__main__":
        run()
    ```

!!! success
    We used `rats.app` to define a container with a couple services, and make a small
    `__main__.py` file to allow us to run the service defined by `PluginServices.MAIN`.

    You can create a script entry in your `pyproject.toml` file to expose your application through
    a terminal command:

    ```toml
    [tool.poetry.scripts]
    foo = "foo.__main__:run"
    ```

### rats.apps

```py linenums="1" title="src/python/rats/apps/__main__.py"
--8<-- "rats-apps/src/python/rats/apps/__main__.py"
```

### rats.annotations
This package helps create decorators meant to attach annotations to functions or methods. The
annotation functions in `rats.apps` are a good example of using this package to create a friendly
developer experience in your own domains.

```py linenums="1" title="src/python/rats/annotations/__main__.py"
--8<-- "rats-apps/src/python/rats/annotations/__main__.py"
```

### rats.cli

```py linenums="1" title="src/python/rats/cli/__main__.py"
--8<-- "rats-apps/src/python/rats/cli/__main__.py"
```

### rats.logs

!!! warning "under constructions"
    COMING SOON

```py linenums="1" title="src/python/rats/logs/__main__.py"
--8<-- "rats-apps/src/python/rats/logs/__main__.py"
```
