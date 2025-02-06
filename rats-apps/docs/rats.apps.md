---
title: rats.apps
---
::: rats.apps
    options:
        heading_level: 1

## Examples

The `rats_e2e.apps` module has a handful of heavily documented tests that serve as good examples
for different types of applications. You can run the cli command at the root of the module with
`python -m rats_e2e.apps` or interact with each example directly.

We try to make each example fully executable by defining an entry point `main()`, the function we
would reference to register a script in `pyproject.toml`; the `__main__.py` file makes the modules
executable directly, like `python -m rats_e2e.apps.[name]`; if the example is of an application, a
`._app.py` file will contain the `Application` class and any relevant service ids; and if the
example contains a plugin container–meant to be loaded by another application–the relevant
`PluginContainer` and service ids will be found in a `._plugin.py` file.

::: rats_e2e.apps.minimal
    options:
        heading_level: 3

::: rats_e2e.apps.inputs
    options:
        heading_level: 3
