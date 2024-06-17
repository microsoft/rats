# rats-apps

The `rats-apps` libraries help create applications. A small set of packages that try to
eliminate some of the most common boilerplate code when creating applications of any kind. Most
other `rats` libraries in this project are developed with help from `rats-apps`.

## rats.apps

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
mechanism.

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

With our newly created plugin group of "foo.plugins", we use `apps.Container` classes to extend
the functionality of the application. We've already registered `foo.PluginContainer` in the
`pyproject.toml` file, so we need to create the class and refresh our virtual environment.

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
    experience, but allow advanced, unplanned uses to adjust most implementation details.

## rats.annotations

## rats.cli

## rats.logs
