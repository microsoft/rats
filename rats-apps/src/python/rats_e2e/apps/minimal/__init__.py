"""
A minimal executable application example.

You can run this example by using the [rats_e2e.apps.minimal.Application][] class within python,
or directly through a terminal.

=== ":material-language-python: python"
    ```python
    from rats import apps
    from rats_e2e.apps import minimal

    apps.run_plugin(minimal.Application)
    ```

=== ":material-console: ~/code"
    ```bash
    python -m rats_e2e.apps.minimal
    ```
"""

from ._app import Application, main

__all__ = [
    "Application",
    "main",
]
