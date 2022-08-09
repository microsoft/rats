import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import TypeVar, Generic, Callable

from azure.devops.connection import Connection
from azure.devops.v6_0.core import CoreClient
from azure.devops.v6_0.work import WorkClient
from azure.devops.v6_0.work_item_tracking import WorkItemTrackingClient
from msrest.authentication import BasicAuthentication

from ._app import AdocliApp, MoveOnCallTicketsCommand
from ._authentication import AdoOauthToken
from ._cli import RawCliRequest
from oneml.logging import LoggingClient
from ._iterations import IterationsClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdoConfig:
    organization_url: str
    project_id: str
    on_call_team_id: str
    redmond_team_id: str
    rednext_team_id: str


ProviderType = TypeVar("ProviderType")


class TypeProvider(Generic[ProviderType]):

    _callback: Callable[[], ProviderType]

    def __init__(self, callback: Callable[[], ProviderType]):
        self._callback = callback

    def __call__(self) -> ProviderType:
        return self._callback()


class AdocliDiContainer:

    _request: RawCliRequest

    def __init__(self, request: RawCliRequest):
        self._request = request

    @lru_cache()
    def cli_app(self) -> AdocliApp:
        return AdocliApp(
            request=self._request,
            iterations_client=self.iterations_client(),
            move_on_call_tickets_command=self.move_on_call_tickets_command(),
        )

    @lru_cache()
    def move_on_call_tickets_command(self) -> MoveOnCallTicketsCommand:
        return MoveOnCallTicketsCommand(iterations_client=self.iterations_client())

    @lru_cache()
    def iterations_client(self) -> IterationsClient:
        return IterationsClient(
            work_item_tracking_client=self._ado_work_item_tracking_client(),
            work_client=self._ado_work_client(),
            project_id=self._config().project_id,
            team_id=self._config().redmond_team_id,
        )

    @lru_cache()
    def logging_client(self) -> LoggingClient:
        return LoggingClient()

    @lru_cache()
    def _ado_core_client_provider(self) -> TypeProvider[CoreClient]:
        return TypeProvider[CoreClient](lambda: self._ado_core_client())

    @lru_cache()
    def _ado_work_client_provider(self) -> TypeProvider[WorkClient]:
        return TypeProvider[WorkClient](lambda: self._ado_work_client())

    @lru_cache()
    def _ado_work_item_tracking_client_provider(self) -> TypeProvider[WorkItemTrackingClient]:
        return TypeProvider[WorkItemTrackingClient](lambda: self._ado_work_item_tracking_client())

    @lru_cache()
    def _ado_core_client(self) -> CoreClient:
        return self._ado_connection().clients_v6_0.get_core_client()

    @lru_cache()
    def _ado_work_client(self) -> WorkClient:
        return self._ado_connection().clients_v6_0.get_work_client()

    @lru_cache()
    def _ado_work_item_tracking_client(self) -> WorkItemTrackingClient:
        return self._ado_connection().clients_v6_0.get_work_item_tracking_client()

    @lru_cache()
    def _ado_connection(self) -> Connection:
        return Connection(base_url=self._config().organization_url, creds=self._ado_credentials())

    @lru_cache()
    def _ado_credentials(self) -> BasicAuthentication:
        return BasicAuthentication('', self._ado_oauth_token().get_token())

    @lru_cache()
    def _ado_oauth_token(self) -> AdoOauthToken:
        return AdoOauthToken()

    @lru_cache()
    def _config(self) -> AdoConfig:
        return AdoConfig(
            organization_url="https://dev.azure.com/immunomics",
            project_id="7dd580c2-fa96-4385-8af5-b58d80de51d9",
            on_call_team_id="e16c13ef-c0cc-4985-8a4a-db34a149692a",
            redmond_team_id="78298ab2-3198-4e7a-aa4f-d8cdb4c19bb1",
            rednext_team_id="fdde3be3-515e-4c03-9259-a5a1f846f6bd",
        )
