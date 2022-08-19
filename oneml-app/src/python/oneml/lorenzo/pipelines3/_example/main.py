# type: ignore
# flake8: noqa
from oneml.lorenzo.pipelines3._example._di_container import Pipeline3DiContainer


def _main() -> None:
    di_container = Pipeline3DiContainer(args=tuple())
    application = di_container.application()
    application.execute()


if __name__ == "__main__":
    _main()
