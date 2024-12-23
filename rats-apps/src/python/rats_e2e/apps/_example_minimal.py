import logging

from rats import apps

logger = logging.getLogger(__name__)


class MinimalExampleApp(apps.AppContainer, apps.PluginMixin):
    def execute(self) -> None:
        print("this is a minimal application")


def main() -> None:
    apps.run_plugin(MinimalExampleApp)


if __name__ == "__main__":
    main()
