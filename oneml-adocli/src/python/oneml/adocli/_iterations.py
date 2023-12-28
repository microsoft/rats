import datetime
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple

from azure.devops.v6_0.work import TeamContext, TeamSettingsIteration, WorkClient
from azure.devops.v6_0.work_item_tracking import (
    JsonPatchOperation,
    WorkItem,
    WorkItemRelation,
    WorkItemTrackingClient,
)

from ._work_items import AdoWorkItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdoIteration:
    id: str
    name: str
    path: str
    start_date: datetime.datetime
    end_date: datetime.datetime

    def __post_init__(self) -> None:
        pass

    def sprint(self) -> int:
        return int(self.name.split(" ")[-1])


class AdoSprintClient:

    _work_item_tracking_client: WorkItemTrackingClient
    _work_client: WorkClient
    _iteration: AdoIteration
    _project_id: str
    _team_id: str

    def __init__(
            self,
            work_item_tracking_client: WorkItemTrackingClient,
            work_client: WorkClient,
            iteration: AdoIteration,
            project_id: str,
            team_id: str):
        self._work_item_tracking_client = work_item_tracking_client
        self._work_client = work_client
        self._iteration = iteration
        self._project_id = project_id
        self._team_id = team_id

    def take_ticket_ownership(self, ticket: AdoWorkItem) -> None:
        on_call_feature = self.get_on_call_feature()
        print(f"ON CALL FEATURE ITERATION: {on_call_feature.iteration_path}")
        work_item = self._work_item_tracking_client.get_work_item(
            ticket.id, project=self._project_id, expand="Relations")

        def find_parent_relation_index(relations: List[WorkItemRelation]) -> int:
            for x, r in enumerate(relations):
                if r.attributes["name"] == "Parent":
                    logger.debug(f"Detected parent relation at index: {x}")
                    return x

            # Better to give up here and let the user resolve this manually.
            raise RuntimeError(f"No Parent Relation Found for Ticket: {ticket}")

        parent_relation_index = find_parent_relation_index(work_item.relations)

        current_url = work_item.relations[parent_relation_index].url
        new_url = "/".join(current_url.split("/")[:-1]) + f"/{on_call_feature.id}"

        if current_url == new_url:
            raise RuntimeError(f"Ticket already owned by expected parent: {ticket}")

        logger.debug(f"Updating parent relation for ticket: {ticket}")
        logger.debug(f"New parent relation for ticket: {new_url}")

        new_relation = {
            "attributes": {"isLocked": False},
            "rel": work_item.relations[parent_relation_index].rel,
            "url": new_url
        }

        logger.debug("")

        document = [
            # This test ensures the card hasn't changed since we last queried DevOps
            JsonPatchOperation(
                op="test",
                path="/rev",
                value=work_item.rev,
            ),
            JsonPatchOperation(
                op="remove",
                path=f"/relations/{parent_relation_index}",
            ),
            JsonPatchOperation(
                op="add",
                path="/relations/-",
                value=new_relation,
            ),
            JsonPatchOperation(
                op="replace",
                path="/fields/System.IterationPath",
                value=on_call_feature.iteration_path,
            ),
        ]

        self._work_item_tracking_client.update_work_item(
            document=document,
            id=ticket.id,
            project=self._project_id,
        )

    def get_on_call_tickets(self) -> Tuple[AdoWorkItem, ...]:
        feature = self._get_on_call_feature_response()

        child_ids = []
        for relation in feature.relations:
            if relation.attributes["name"] == "Child":
                child_ids.append(int(relation.url.split("/")[-1]))

        if not len(child_ids):
            return tuple()

        tickets = self._work_item_tracking_client.get_work_items(child_ids)
        result = []
        for ticket in tickets:
            result.append(AdoWorkItem(
                id=ticket.id,
                title=ticket.fields["System.Title"],
                description=ticket.fields.get("System.Description", ""),
                iteration_path=ticket.fields["System.IterationPath"],
                state=ticket.fields["System.State"],
            ))

        return tuple(result)

    def get_on_call_feature(self) -> AdoWorkItem:
        feature = self._get_on_call_feature_response()

        return AdoWorkItem(
            id=feature.id,
            title=feature.fields["System.Title"],
            description=feature.fields.get("System.Description", ""),
            state=feature.fields["System.State"],
            iteration_path=feature.fields["System.IterationPath"],
        )

    @lru_cache()
    def _get_on_call_feature_response(self) -> WorkItem:
        features = self._get_sprint_features()
        for feature in features:
            if feature.fields["System.Title"] == f"On Call: Sprint {self._iteration.sprint()}":
                return feature

        raise RuntimeError(f"On Call Feature Not Found for Sprint({self._iteration.sprint()})")

    @lru_cache()
    def _get_sprint_features(self) -> Tuple[WorkItem, ...]:
        features = []
        for item in self._get_sprint_work_items():
            if item.fields["System.WorkItemType"] == "Feature":
                features.append(item)

        return tuple(features)

    @lru_cache()
    def _get_sprint_work_items(self) -> Tuple[WorkItem, ...]:
        item_ids = self._get_sprint_work_item_ids()
        if not len(item_ids):
            return tuple()

        return tuple(self._work_item_tracking_client.get_work_items(item_ids, expand="Relations"))

    @lru_cache()
    def _get_sprint_work_item_ids(self) -> List[int]:
        tc = TeamContext(project_id=self._project_id, team_id=self._team_id)
        iteration_items = self._work_client.get_iteration_work_items(
            team_context=tc,
            iteration_id=self._iteration.id,
        )

        ids = []
        for item in iteration_items.work_item_relations:
            ids.append(item.target.id)

        return ids


class IterationsClient:

    _work_item_tracking_client: WorkItemTrackingClient
    _work_client: WorkClient
    _project_id: str
    _team_id: str

    def __init__(
            self,
            work_item_tracking_client: WorkItemTrackingClient,
            work_client: WorkClient,
            project_id: str,
            team_id: str):
        self._work_item_tracking_client = work_item_tracking_client
        self._work_client = work_client
        self._project_id = project_id
        self._team_id = team_id

    def get_previous_iteration(self) -> AdoIteration:
        current = self.get_current_iteration()
        return self.get_iteration_for_sprint(current.sprint() - 1)

    def get_next_iteration(self) -> AdoIteration:
        current = self.get_current_iteration()
        return self.get_iteration_for_sprint(current.sprint() + 1)

    def get_current_iteration(self) -> AdoIteration:
        for i in self._get_responses():
            if i.attributes.time_frame == "current":
                return self._cast(i)

        raise RuntimeError("Current Iteration Not Found")

    def get_iteration_for_sprint(self, sprint: int):
        for i in self._get_responses():
            entity = self._cast(i)
            if entity.sprint() == sprint:
                return entity

        raise RuntimeError(f"Iteration for Sprint({sprint}) Not Found")

    @lru_cache()
    def get_iterations(self) -> List[AdoIteration]:
        iterations = self._get_responses()

        result = []
        for i in iterations:
            result.append(self._cast(i))

        return result

    def get_sprint_client(self, sprint: int) -> AdoSprintClient:
        return AdoSprintClient(
            work_item_tracking_client=self._work_item_tracking_client,
            work_client=self._work_client,
            iteration=self.get_iteration_for_sprint(sprint),
            project_id=self._project_id,
            team_id=self._team_id,
        )

    def _cast(self, response: TeamSettingsIteration) -> AdoIteration:
        return AdoIteration(
            id=response.id,
            name=response.name,
            path=response.path,
            start_date=response.attributes.start_date,
            end_date=response.attributes.finish_date,
        )

    @lru_cache()
    def _get_responses(self) -> List[TeamSettingsIteration]:
        tc = TeamContext(project_id=self._project_id, team_id=self._team_id)
        return self._work_client.get_team_iterations(tc)
