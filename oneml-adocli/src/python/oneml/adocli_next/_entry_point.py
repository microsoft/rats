from oneml.app import OnemlApp
from ._pipelines import AdocliPipelines


def main() -> None:
    app = OnemlApp.default()
    # app.run(executable(lambda: print("Hello, world")))
    app.run_pipeline(AdocliPipelines.HELLO_WORLD)
