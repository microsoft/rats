import logging

from immunodata.datasets import IDatasetClient
from immunodata.datasets.immunocli import ImmunodataDatasetsContainer

from oneml.app import AppPlugin
from oneml.habitats.immunocli import OnemlHabitatsImmunocliServices
from oneml.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_provider,
)

from ._ampds_uri_service import (
    ComposeAmpdsUriFromCommit,
    ComposeAmpdsUriFromReadSpecifications,
    IComposeAmpdsUriFromCommit,
    IComposeAmpdsUriFromReadSpecifications,
    IParseAmpdsUriForRead,
    IParseAmpdsUriForWrite,
    ParseAmpdsUriForRead,
    ParseAmpdsUriForWrite,
)
from ._blob_store_base_location_service import (
    DatasetBlobStoreBaseLocationService,
    IDatasetBlobStoreBaseLocationService,
)
from ._prepare_and_publish_service import (
    DatasetPrepareAndPublishService,
    IDatasetPrepareAndPublishService,
)
from ._publish_service import DatasetPublishService, IDatasetPublishService
from ._read_commit_service import DatasetReadCommitService, IDatasetReadCommitService
from ._write_storage_location_service import (
    DatasetWriteStorageLocationService,
    IDatasetWriteStorageLocationService,
)

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    DATASET_BLOB_STORE_BASE_LOCATION = ServiceId[IDatasetBlobStoreBaseLocationService](
        "dataset-blob-store-base-location"
    )
    DATASET_READ_COMMIT = ServiceId[IDatasetReadCommitService]("dataset-read-commit")
    DATASET_WRITE_STORAGE_LOCATION = ServiceId[IDatasetWriteStorageLocationService](
        "dataset-write-storage-location"
    )
    DATASET_PUBLISH = ServiceId[IDatasetPublishService]("dataset-publish")
    PARSE_AMPDS_URI_FOR_READ = ServiceId[IParseAmpdsUriForRead]("parse-ampds-uri-for-read")
    PARSE_AMPDS_URI_FOR_WRITE = ServiceId[IParseAmpdsUriForWrite]("parse-ampds-uri-for-write")
    COMPOSE_AMPDS_URI_FROM_READ_SPECIFICATIONS = ServiceId[IComposeAmpdsUriFromReadSpecifications](
        "compose-ampds-uri-from-read-specifications"
    )
    COMPOSE_AMPDS_URI_FROM_COMMIT = ServiceId[IComposeAmpdsUriFromCommit](
        "compose-ampds-uri-from-commit"
    )
    DATASET_PREPARE_AND_PUBLISH = ServiceId[IDatasetPrepareAndPublishService](
        "dataset-prepare-and-publish"
    )


class OnemlHabitatsDatasetsDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.DATASET_PREPARE_AND_PUBLISH)
    def dataset_prepare_service(self) -> DatasetPrepareAndPublishService:
        return DatasetPrepareAndPublishService(
            parse_ampds_uri_for_read=self._app.get_service(
                _PrivateServices.PARSE_AMPDS_URI_FOR_READ
            ),
            parse_ampds_uri_for_write=self._app.get_service(
                _PrivateServices.PARSE_AMPDS_URI_FOR_WRITE
            ),
            dataset_read_commit=self._app.get_service(_PrivateServices.DATASET_READ_COMMIT),
            dataset_write_storage_location=self._app.get_service(
                _PrivateServices.DATASET_WRITE_STORAGE_LOCATION
            ),
            dataset_publish=self._app.get_service(_PrivateServices.DATASET_PUBLISH),
            compose_ampds_uri_from_commit=self._app.get_service(
                _PrivateServices.COMPOSE_AMPDS_URI_FROM_COMMIT
            ),
        )

    def _dataset_client(self) -> IDatasetClient:
        locate_habitats_cli_di_containers = self._app.get_service(
            OnemlHabitatsImmunocliServices.LOCATE_HABITATS_CLI_DI_CONTAINERS
        )
        datasets_container = locate_habitats_cli_di_containers(ImmunodataDatasetsContainer)
        dataset_client = datasets_container.dataset_client()
        return dataset_client

    @service_provider(_PrivateServices.DATASET_WRITE_STORAGE_LOCATION)
    def dataset_write_storage_location_service(self) -> DatasetWriteStorageLocationService:
        return DatasetWriteStorageLocationService(
            blob_store_base_location_service=self._app.get_service(
                _PrivateServices.DATASET_BLOB_STORE_BASE_LOCATION
            ),
        )

    @service_provider(_PrivateServices.DATASET_READ_COMMIT)
    def dataset_read_commit_service(self) -> DatasetReadCommitService:
        return DatasetReadCommitService(
            dataset_client=self._dataset_client(),
        )

    @service_provider(_PrivateServices.DATASET_PUBLISH)
    def dataset_publish_service(self) -> DatasetPublishService:
        return DatasetPublishService(
            dataset_client=self._dataset_client(),
        )

    @service_provider(_PrivateServices.PARSE_AMPDS_URI_FOR_READ)
    def parse_ampds_uri_for_read_service(self) -> ParseAmpdsUriForRead:
        return ParseAmpdsUriForRead()

    @service_provider(_PrivateServices.PARSE_AMPDS_URI_FOR_WRITE)
    def parse_ampds_uri_for_write_service(self) -> ParseAmpdsUriForWrite:
        return ParseAmpdsUriForWrite()

    @service_provider(_PrivateServices.COMPOSE_AMPDS_URI_FROM_READ_SPECIFICATIONS)
    def compose_ampds_uri_from_read_specifications_service(
        self,
    ) -> ComposeAmpdsUriFromReadSpecifications:
        return ComposeAmpdsUriFromReadSpecifications()

    @service_provider(_PrivateServices.COMPOSE_AMPDS_URI_FROM_COMMIT)
    def compose_ampds_uri_from_commit_service(self) -> ComposeAmpdsUriFromCommit:
        return ComposeAmpdsUriFromCommit()

    @service_provider(_PrivateServices.DATASET_BLOB_STORE_BASE_LOCATION)
    def dataset_blob_store_base_location_service(self) -> DatasetBlobStoreBaseLocationService:
        return DatasetBlobStoreBaseLocationService()


class OnemlHabitatsDatasetsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-habitats-datasets plugin")
        app.parse_service_container(OnemlHabitatsDatasetsDiContainer(app))


class OnemlHabitatsDatasetsServices:
    DATASET_PREPARE_AND_PUBLISH = _PrivateServices.DATASET_PREPARE_AND_PUBLISH
