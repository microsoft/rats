from typing import NamedTuple

import yaml

from rats import apps

from ._texts import ExampleTexts


@apps.autoscope
class PluginDatasets:
    RANDOM_TEXTS = apps.ServiceId[ExampleTexts]("random-texts")


@apps.autoscope
class PluginServices:
    MAIN_EXE = apps.ServiceId[apps.Executable]("main-exe")
    DATASETS = PluginDatasets


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.MAIN_EXE)
    def _main_exe(self) -> apps.Executable:
        def run() -> None:
            def _named_tuple(s, data: NamedTuple):
                if hasattr(data, "_asdict"):
                    return s.represent_dict(data._asdict())
                return s.represent_list(data)

            yaml.SafeDumper.yaml_multi_representers[tuple] = _named_tuple
            texts = self._app.get(PluginServices.DATASETS.RANDOM_TEXTS)
            print(yaml.safe_dump(texts.books(1)))

        return apps.App(run)

    @apps.service(PluginServices.DATASETS.RANDOM_TEXTS)
    def _random_texts(self) -> ExampleTexts:
        return ExampleTexts()
