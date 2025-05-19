import os

from rats import apps as apps
from rats import runtime


class ExampleJob(apps.AppContainer, apps.PluginMixin):
    def execute(self) -> None:
        print("hello, world!")
        context_collection = self._app.get(runtime.AppServices.CONTEXT)
        print("loaded context:")
        for item in context_collection.items:
            print(f"{item.service_id} -> {item.values}")

        print("rats envs:")
        for k, v in os.environ.items():
            if k.startswith("RATS_"):
                print(f"{k} → {v}")
