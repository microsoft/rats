import os

from rats import aml as aml
from rats import apps as apps


class Application(apps.AppContainer, apps.PluginMixin):
    def execute(self) -> None:
        print("hello, world!")
        context_collection = self._app.get(aml.AppConfigs.CONTEXT_COLLECTION)
        print("loaded context:")
        for item in context_collection.items:
            print(f"{item.service_id} -> {item.values}")

        print("rats envs:")
        for k, v in os.environ.items():
            if k.startswith("RATS_"):
                print(f"{k} → {v}")
