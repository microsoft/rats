from collections.abc import Callable, Iterable, Mapping
from typing import NamedTuple, TypedDict

from rats import apps

from .._legacy_subpackages import typing as rpt


class PipelineRegistryEntry(TypedDict):
    name: str
    doc: str
    service_id: apps.ServiceId[rpt.UPipeline]


class RegisteredPipeline(NamedTuple):
    name: str
    doc: str
    provider: Callable[[], rpt.UPipeline]


IPipelineRegistry = Mapping[str, RegisteredPipeline]


class PipelineRegistry(Mapping[str, RegisteredPipeline]):
    _app: apps.Container
    _entries: dict[str, PipelineRegistryEntry]

    def __init__(self, app: apps.Container, entries: Iterable[PipelineRegistryEntry]):
        self._app = app
        self._entries = {entry["name"]: entry for entry in entries}

    def __getitem__(self, key: str) -> RegisteredPipeline:
        entry = self._entries[key]
        return RegisteredPipeline(
            name=entry["name"],
            doc=entry["doc"],
            provider=lambda: self._app.get(entry["service_id"]),
        )

    def __iter__(self):
        return iter(self._entries)

    def __len__(self):
        return len(self._entries)
