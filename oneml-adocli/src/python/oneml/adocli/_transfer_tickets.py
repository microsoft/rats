import logging

from ._iterations import AdoSprintClient

logger = logging.getLogger(__name__)


class TransferUnfinishedTicketsUseCase:

    _source_sprint_client: AdoSprintClient
    _destination_sprint_client: AdoSprintClient

    def __init__(
            self,
            source_sprint_client: AdoSprintClient,
            destination_sprint_client: AdoSprintClient) -> None:
        self._source_sprint_client = source_sprint_client
        self._destination_sprint_client = destination_sprint_client

    def execute(self) -> None:
        source_on_call_tickets = self._source_sprint_client.get_on_call_tickets()

        for ticket in source_on_call_tickets:
            if ticket.is_done():
                logger.debug(f"Skipping completed ticket: [{ticket.id}] {ticket.title}")
                continue

            self._destination_sprint_client.take_ticket_ownership(ticket)
