from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator

from ..services import IProvideServices, ServiceId
from ._io_data import (
    IFormatUri,
    ILoadPipelineData,
    IManageLoaders,
    IManagePublishers,
    IPublishPipelineData,
    PipelineDataId,
)
from ._rw_data import DataType, DataType_co, DataType_contra, IReadData, IWriteData, RWDataUri


class InMemoryUriFormatter(IFormatUri[DataType]):
    def __call__(self, data_id: PipelineDataId[DataType]) -> RWDataUri:
        return RWDataUri(str(data_id))


class FilesystemUriFormatter(IFormatUri[DataType]):
    _path: Path

    def __init__(self, path: Path) -> None:
        self._path = path

    def __call__(self, data_id: PipelineDataId[DataType]) -> RWDataUri:
        return RWDataUri(str(self._path / str(data_id)))


class PipelineDataLoader(ILoadPipelineData[DataType_co]):
    _data_id: PipelineDataId[DataType_co]
    _reader: IReadData[DataType_co]
    _uri_formatter: IFormatUri[DataType_co]

    def __init__(
        self,
        data_id: PipelineDataId[DataType_co],
        reader: IReadData[DataType_co],
        uri_formatter: IFormatUri[DataType_co],
    ) -> None:
        self._data_id = data_id
        self._reader = reader
        self._uri_formatter = uri_formatter

    def load(self) -> DataType_co:
        uri = self._uri_formatter(self._data_id)
        return self._reader.read(uri)


class PipelineDataPublisher(IPublishPipelineData[DataType_contra]):
    _data_id: PipelineDataId[DataType_contra]
    _writer: IWriteData[DataType_contra]
    _uri_formatter: IFormatUri[DataType_contra]

    def __init__(
        self,
        data_id: PipelineDataId[DataType_contra],
        writer: IWriteData[DataType_contra],
        uri_formatter: IFormatUri[DataType_contra],
    ) -> None:
        self._data_id = data_id
        self._writer = writer
        self._uri_formatter = uri_formatter

    def publish(self, payload: DataType_contra) -> None:
        uri = self._uri_formatter(self._data_id)
        self._writer.write(uri, payload)


class PipelineLoaderGetter(IManageLoaders[DataType]):
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
        input_data_id: PipelineDataId[DataType],
        output_data_id: PipelineDataId[DataType],
        uri_formatter_id: ServiceId[IFormatUri[DataType]],
        reader_id: ServiceId[IReadData[DataType_co]],
    ) -> None:
        self._loaders[input_data_id] = (output_data_id, uri_formatter_id, reader_id)

    def get(self, data_id: PipelineDataId[DataType]) -> ILoadPipelineData[DataType]:
        output_data_id, uri_formatter_id, reader_id = self._loaders[data_id]
        uri_formatter = self._services.get_service(uri_formatter_id)
        reader = self._services.get_service(reader_id)
        return PipelineDataLoader(output_data_id, reader, uri_formatter)


class PublisherCollection(IPublishPipelineData[DataType_contra]):
    _publishers: tuple[IPublishPipelineData[DataType_contra], ...]

    def __init__(self, publishers: Iterable[IPublishPipelineData[DataType_contra]]) -> None:
        self._publishers = tuple(publishers)

    def publish(self, payload: DataType_contra) -> None:
        for publisher in self._publishers:
            publisher.publish(payload)


class PipelinePublisherGetter(IManagePublishers[DataType]):
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
        data_id: PipelineDataId[DataType],
        uri_formatter_id: ServiceId[IFormatUri[DataType]],
        writer_id: ServiceId[IWriteData[DataType]],
    ) -> None:
        self._publishers[data_id].append((uri_formatter_id, writer_id))

    def get(self, data_id: PipelineDataId[DataType]) -> IPublishPipelineData[DataType]:
        return PublisherCollection(self._get_iterator(data_id))

    def _get_iterator(
        self, data_id: PipelineDataId[DataType]
    ) -> Iterator[IPublishPipelineData[DataType]]:
        for uri_formatter_id, writer_id in self._publishers[data_id]:
            uri_formatter = self._services.get_service(uri_formatter_id)
            writer = self._services.get_service(writer_id)
            yield PipelineDataPublisher(data_id, writer, uri_formatter)
