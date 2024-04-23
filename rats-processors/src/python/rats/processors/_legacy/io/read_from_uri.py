import logging
from abc import abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Generic, Protocol, TypeVar
from urllib.parse import urlparse, urlunparse

from typing_extensions import TypedDict

from rats.io import IReadData, RWDataUri
from rats.services import IProvideServices, ServiceId

from ..ux import UPipeline, UPipelineBuilder
from ._manifest import JsonFormattable, Manifest
from .type_rw_mappers import IGetReadServicesForType

logger = logging.getLogger(__name__)

DataType = TypeVar("DataType")
ODataType = TypeVar("ODataType")


class ReadFromUriProcessorOutput(TypedDict):
    data: DataType  # type: ignore[valid-type]


def _is_relative_path(url: str | None) -> bool:
    if url is None:
        return True
    parsed = urlparse(url)
    if parsed.hostname:
        return False
    if Path(parsed.path).is_absolute():
        return False
    if Path(url).is_absolute():
        return False
    return True


class ReadFromUriProcessor(Generic[DataType]):
    _service_provider: IProvideServices
    _read_service_ids: Mapping[str, ServiceId[IReadData[DataType]]]
    _read_manifest_service_ids: Mapping[str, ServiceId[IReadData[JsonFormattable]]]
    _uri: str

    def __init__(
        self,
        service_provider: IProvideServices,
        read_service_ids: Mapping[str, ServiceId[IReadData[DataType]]],
        read_manifest_service_ids: Mapping[str, ServiceId[IReadData[JsonFormattable]]],
        uri: str,
    ) -> None:
        self._service_provider = service_provider
        self._read_service_ids = read_service_ids
        self._read_manifest_service_ids = read_manifest_service_ids
        self._uri = uri

    def _read(
        self, uri: str, read_service_ids: Mapping[str, ServiceId[IReadData[ODataType]]]
    ) -> ODataType:
        logger.debug(f"Reading from uri: {uri}")
        parsed_uri = urlparse(uri)
        fragment = parsed_uri.fragment
        if fragment:
            logger.debug(f"Fragment found: {fragment}")
            # if given a fragment, it is assumed that the uri points to a manifest, and the
            # fragment is the key within the manifest, pointing to a either different uri, or
            # a path relative to the manifest uri
            # first we'll construct the manifest uri, by removing the fragment:
            manifest_uri = urlunparse(parsed_uri._replace(fragment=""))
            logger.debug(
                f"Assuming {manifest_uri} points to a manifest json file, that {fragment} is a "
                + "key within it, and the the value is either a uri or a relative path to the "
                + "manifest uri."
            )
            # recursively read the manifest:
            path_from_manifest = self._read(manifest_uri, self._read_manifest_service_ids)
            # find the value associated with the fragment key:
            try:
                for key in fragment.split("."):
                    path_from_manifest = path_from_manifest[key]  # type: ignore[index]
                    logger.debug(f"Found key {key}.")
            except KeyError:
                raise ValueError(f"Fragment: {fragment} is not a key in the manifest.") from None
            if not isinstance(path_from_manifest, str):
                raise ValueError(
                    f"Fragment: {fragment} is a key in the manifest, but the associated value is "
                    + "not a string."
                )
            logger.debug(f"Found path in manifest: {path_from_manifest}")
            # if path is an absolute uri, we'll use it as is, otherwise we'll construct the
            # absolute uri by joining the manifest uri with the relative path:
            if _is_relative_path(path_from_manifest):
                logger.debug(f"Path is relative, joining with manifest uri: {manifest_uri}")
                # find the directory of the manifest uri:
                manifest_dir = Path(parsed_uri.path).parent
                # join the manifest dir with the relative path:
                path = str(manifest_dir / path_from_manifest)
                parsed_uri = parsed_uri._replace(path=path)._replace(fragment="")
                uri = urlunparse(parsed_uri)
                logger.debug(f"Constructed uri: {uri}")
            else:
                logger.debug(f"Path is absolute, using as is: {path_from_manifest}")
                uri = path_from_manifest

            return self._read(uri, read_service_ids)
        else:
            scheme = parsed_uri.scheme
            read_service_id = read_service_ids.get(scheme, None)
            if read_service_id is None:
                raise ValueError(f"Unsupported scheme: {scheme}")
            reader = self._service_provider.get_service(read_service_id)
            return reader.read(RWDataUri(uri))

    def process(self) -> ReadFromUriProcessorOutput:
        return ReadFromUriProcessorOutput(data=self._read(self._uri, self._read_service_ids))


class IReadFromUriPipelineBuilder(Protocol):
    @abstractmethod
    def build(self, data_type: type[DataType], uri: str | None = None) -> UPipeline: ...


class ReadFromUriPipelineBuilder(IReadFromUriPipelineBuilder):
    _service_provider_service_id: ServiceId[IProvideServices]
    _get_read_services_for_type: IGetReadServicesForType

    def __init__(
        self,
        service_provider_service_id: ServiceId[IProvideServices],
        get_read_services_for_type: IGetReadServicesForType,
    ) -> None:
        self._service_provider_service_id = service_provider_service_id
        self._get_read_services_for_type = get_read_services_for_type

    def build(self, data_type: type[DataType], uri: str | None = None) -> UPipeline:
        read_service_ids = self._get_read_services_for_type.get_read_service_ids(data_type)
        read_manifest_service_ids = self._get_read_services_for_type.get_read_service_ids(Manifest)
        config = {
            k: v
            for k, v in dict(
                read_service_ids=read_service_ids,
                read_manifest_service_ids=read_manifest_service_ids,
                uri=uri,
            ).items()
            if v is not None
        }
        task = UPipelineBuilder.task(
            processor_type=ReadFromUriProcessor,
            config=config,
            services=dict(service_provider=self._service_provider_service_id),
        )
        return task
