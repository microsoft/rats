import logging
from argparse import ArgumentParser, Namespace

from ._cli import RawCliRequest
from ._iterations import IterationsClient
from ._transfer_tickets import TransferUnfinishedTicketsUseCase

logger = logging.getLogger(__name__)


class MoveOnCallTicketsCommand:

    _iterations_client: IterationsClient

    def __init__(self, iterations_client: IterationsClient):
        self._iterations_client = iterations_client

    def execute(self, from_sprint: int | None = None, to_sprint: int | None = None) -> None:
        if not from_sprint:
            from_sprint = self._iterations_client.get_current_iteration().sprint()

        if not to_sprint:
            to_sprint = from_sprint + 1

        current_sprint_client = self._iterations_client.get_sprint_client(from_sprint)
        next_sprint_client = self._iterations_client.get_sprint_client(to_sprint)

        print(f"Current Sprint: {from_sprint}")
        print(f"Next Sprint: {to_sprint}")

        current_on_call_feature = current_sprint_client.get_on_call_feature()
        current_on_call_tickets = current_sprint_client.get_on_call_tickets()

        print(
            f"Current Sprint Feature: [{current_on_call_feature.state}] {current_on_call_feature.title}")
        if len(current_on_call_tickets):
            print("Current Sprint Tickets:")
            for ticket in current_on_call_tickets:
                print(f"\t [{ticket.state}] {ticket.title}")
        else:
            print("Current Sprint Tickets: NONE")

        next_on_call_feature = next_sprint_client.get_on_call_feature()
        next_on_call_tickets = next_sprint_client.get_on_call_tickets()

        print(
            f"Next Sprint Feature: [{next_on_call_feature.state}] {next_on_call_feature.title}")
        if len(next_on_call_tickets):
            print("Next Sprint Tickets:")
            for ticket in next_on_call_tickets:
                print(f"\t [{ticket.state}] {ticket.title}")
        else:
            print("Next Sprint Tickets: NONE")

        transfer_use_case = TransferUnfinishedTicketsUseCase(
            source_sprint_client=current_sprint_client,
            destination_sprint_client=next_sprint_client,
        )
        transfer_use_case.execute()


class AdocliApp:

    _request: RawCliRequest
    _iterations_client: IterationsClient
    _move_on_call_tickets_command: MoveOnCallTicketsCommand

    def __init__(
            self,
            request: RawCliRequest,
            iterations_client: IterationsClient,
            move_on_call_tickets_command: MoveOnCallTicketsCommand):
        self._request = request
        self._iterations_client = iterations_client
        self._move_on_call_tickets_command = move_on_call_tickets_command

    def execute(self) -> None:
        argparser = ArgumentParser(prog=self._request.argv[0].split("/")[-1])

        commands = argparser.add_subparsers(title="Commands", metavar="", dest="command")
        sprint = commands.add_parser(
            name="update-goalie-sprint",
            help="set the active sprint for goalie work.",
        )
        # backlog = commands.add_parser(
        #     name="manage-goalie-backlog",
        #     help="update goalie tickets in the backlog.",
        # )

        sprint.add_argument(
            "--from",
            type=int,
            help="the sprint number that contains goalie cards.",
        )
        sprint.add_argument(
            "--to",
            type=int,
            help="the sprint number we want to move goalie cards to.",
        )

        args = argparser.parse_args(self._request.argv[1:])

        {
            None: lambda a: None,
            "update-goalie-sprint": self._update_goalie_sprint,
            "manage-goalie-backlog": self._manage_goalie_backlog,
        }[args.command](args)

    def _update_goalie_sprint(self, args: Namespace) -> None:
        d = vars(args)
        self._move_on_call_tickets_command.execute(d["from"], d["to"])

    def _manage_goalie_backlog(self, args: Namespace) -> None:
        pass

        # project = core_client.get_project(project_id)
        # print(json.dumps(project.as_dict(), indent=2))
        #
        # teams = core_client.get_teams(project_id)
        # for team in teams:
        #     print(json.dumps(team.as_dict(), indent=2))

        # on_call_project_card = work_item_tracking_client.get_work_item(
        #     on_call_project_card_id, project=project_id, expand="Relations")
        #
        # print(json.dumps(on_call_project_card.as_dict(), indent=2))
        #
        # for project_relation in on_call_project_card.relations:
        #     is_child_epic = project_relation.attributes["name"] == "Child"
        #     if not is_child_epic:
        #         continue
        #
        #     # TODO: I'm assuming the SDK has a way to get this without parsing a URL
        #     epic_card_id = int(project_relation.url.split("/")[-1])
        #     print(epic_card_id, project_relation)
        #
        #     epic_card = work_item_tracking_client.get_work_item(
        #         epic_card_id, project=project_id, expand="Relations")
        #
        #     print(json.dumps(epic_card.as_dict(), indent=2))
        #
        #     for epic_relation in epic_card.relations:
        #         is_child_feature = epic_relation.attributes["name"] == "Child"
        #         if not is_child_feature:
        #             continue
        #
        #         # TODO: I'm assuming the SDK has a way to get this without parsing a URL
        #         feature_card_id = int(epic_relation.url.split("/")[-1])
        #         print(feature_card_id, epic_relation)
        #
        #         feature_card = work_item_tracking_client.get_work_item(
        #             feature_card_id, project=project_id, expand="Relations")
        #
        #         print(json.dumps(feature_card.as_dict(), indent=2))
