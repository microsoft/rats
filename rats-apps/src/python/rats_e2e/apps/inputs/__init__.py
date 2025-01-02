"""
Application using services expected to be provided externally.

Instead of using the `RATS_E2E_NUM_VALUES` environment variable, this application introduces a
small configuration object [rats_e2e.apps.inputs.AppInput][] that we can specify when running
things.

```python
from rats import apps
from rats_e2e.apps import inputs


class AppContext(apps.Container, apps.PluginMixin):
    @apps.service(inputs.AppServices.INPUT)
    def _input(self) -> inputs.AppInput:
        return inputs.AppInput(randint(0, 5))


ctx = ExampleContextContainer(apps.AppContext())
apps.run(apps.AppBundle(app_plugin=inputs.Application, context=ctx))
```
"""

from ._app import AppInput, Application, AppServices, main

__all__ = [
    "AppInput",
    "AppServices",
    "Application",
    "main",
]
