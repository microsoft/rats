import logging
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from furl import furl

from rats.services import IProvideServices, ServiceId

from ._io_data import (
    IFormatUri,
    ILoadPipelineData,
    IManageLoaders,
    IManagePublishers,
    IPublishPipelineData,
    PipelineDataId,
)
from ._rw_data import IReadData, IWriteData, RWDataUri, T_DataType, Tco_DataType, Tcontra_DataType

logger = logging.getLogger(__name__)


class InMemoryUriFormatter(IFormatUri[T_DataType]):
    def __call__(self, data_id: PipelineDataId[T_DataType]) -> RWDataUri:
        # TODO: if we use `scheme://path`, we can use the urlparse lib
        uri = str(furl().set(scheme="memory").set(path=f"{data_id}").url)  # type: ignore
        return RWDataUri(uri)


class FilesystemUriFormatter(IFormatUri[T_DataType]):
    _path: Path

    def __init__(self, path: Path) -> None:
        self._path = path

    def __call__(self, data_id: PipelineDataId[T_DataType]) -> RWDataUri:
        return RWDataUri(str(self._path / str(data_id)))


class PipelineDataLoader(ILoadPipelineData[Tco_DataType]):
    _data_id: PipelineDataId[Tco_DataType]
    _reader: IReadData[Tco_DataType]
    _uri_formatter: IFormatUri[Tco_DataType]

    def __init__(
        self,
        data_id: PipelineDataId[Tco_DataType],
        reader: IReadData[Tco_DataType],
        uri_formatter: IFormatUri[Tco_DataType],
    ) -> None:
        self._data_id = data_id
        self._reader = reader
        self._uri_formatter = uri_formatter

    def load(self) -> Tco_DataType:
        uri = self._uri_formatter(self._data_id)
        return self._reader.read(uri)


class PipelineDataPublisher(IPublishPipelineData[Tcontra_DataType]):
    _data_id: PipelineDataId[Tcontra_DataType]
    _writer: IWriteData[Tcontra_DataType]
    _uri_formatter: IFormatUri[Tcontra_DataType]

    def __init__(
        self,
        data_id: PipelineDataId[Tcontra_DataType],
        writer: IWriteData[Tcontra_DataType],
        uri_formatter: IFormatUri[Tcontra_DataType],
    ) -> None:
        self._data_id = data_id
        self._writer = writer
        self._uri_formatter = uri_formatter

    def publish(self, payload: Tcontra_DataType) -> None:
        uri = self._uri_formatter(self._data_id)
        self._writer.write(uri, payload)


class PipelineLoaderGetter(IManageLoaders[T_DataType]):
    _services: IProvideServices
    _loaders: dict[
        PipelineDataId[Any],
        tuple[PipelineDataId[Any], ServiceId[IFormatUri[Any]], ServiceId[IReadData[Any]]],
    ]

    def __init__(self, services: IProvideServices) -> None:
        self._services = services
        self._loaders = {}

    def register(
        self,
        input_data_id: PipelineDataId[T_DataType],
        output_data_id: PipelineDataId[T_DataType],
        uri_formatter_id: ServiceId[IFormatUri[T_DataType]],
        reader_id: ServiceId[IReadData[Tco_DataType]],
    ) -> None:
        self._loaders[input_data_id] = (output_data_id, uri_formatter_id, reader_id)

    def get(self, data_id: PipelineDataId[T_DataType]) -> ILoadPipelineData[T_DataType]:
        output_data_id, uri_formatter_id, reader_id = self._loaders[data_id]
        uri_formatter = self._services.get_service(uri_formatter_id)
        reader = self._services.get_service(reader_id)
        return PipelineDataLoader(output_data_id, reader, uri_formatter)


class PublisherCollection(IPublishPipelineData[Tcontra_DataType]):
    _publishers: tuple[IPublishPipelineData[Tcontra_DataType], ...]

    def __init__(self, publishers: Iterable[IPublishPipelineData[Tcontra_DataType]]) -> None:
        self._publishers = tuple(publishers)

    def publish(self, payload: Tcontra_DataType) -> None:
        for publisher in self._publishers:
            publisher.publish(payload)


class PipelinePublisherGetter(IManagePublishers[T_DataType]):
    _services: IProvideServices
    _publishers: defaultdict[
        PipelineDataId[Any],
        list[tuple[ServiceId[IFormatUri[Any]], ServiceId[IWriteData[Any]]]],
    ]

    def __init__(self, services: IProvideServices) -> None:
        self._services = services
        self._publishers = defaultdict(list)

    def register(
        self,
        data_id: PipelineDataId[T_DataType],
        uri_formatter_id: ServiceId[IFormatUri[T_DataType]],
        writer_id: ServiceId[IWriteData[T_DataType]],
    ) -> None:
        logger.debug(f"registering publisher {writer_id}")
        self._publishers[data_id].append((uri_formatter_id, writer_id))

    def get(self, data_id: PipelineDataId[T_DataType]) -> IPublishPipelineData[T_DataType]:
        return PublisherCollection(self._get_iterator(data_id))

    def _get_iterator(
        self, data_id: PipelineDataId[T_DataType]
    ) -> Iterator[IPublishPipelineData[T_DataType]]:
        for uri_formatter_id, writer_id in self._publishers[data_id]:
            uri_formatter = self._services.get_service(uri_formatter_id)
            writer = self._services.get_service(writer_id)
            yield PipelineDataPublisher(data_id, writer, uri_formatter)
