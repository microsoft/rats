from rats.app import RatsApp

from ._pipelines import AdocliPipelines


def main() -> None:
    app = RatsApp.default()
    # app.run(executable(lambda: print("Hello, world")))
    app.run_pipeline(AdocliPipelines.HELLO_WORLD)
