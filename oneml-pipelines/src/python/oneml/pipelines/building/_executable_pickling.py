import logging
from abc import abstractmethod
from typing import Protocol

import dill

from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.data._filesystem import IManageFiles
from oneml.pipelines.session import PipelineSessionClient

logger = logging.getLogger(__name__)


class PickleableExecutable(Protocol):
    @abstractmethod
    def execute(self, session: PipelineSessionClient) -> None:
        """"""


class ExecutablePicklingClient:

    _fs_client: IManageFiles

    def __init__(
        self,
        fs_client: IManageFiles,
    ) -> None:
        self._fs_client = fs_client

    def load_active_node(self) -> PickleableExecutable:
        raise NotImplementedError()
        # node = self._session_context.get_context().session_executables_client().get_active_node()
        # return self.load(node)

    def load(self, node: PipelineNode) -> PickleableExecutable:
        path = self._get_data_path(node)
        logger.debug(f"Loading executable for node {node.key} from {path}")
        return dill.loads(self._fs_client.read(path))

    def save_active_node(self, executable: PickleableExecutable) -> None:
        raise NotImplementedError()
        # node = self._session_context.get_context().session_executables_client().get_active_node()
        # self.save(node, executable)

    def save(self, node: PipelineNode, executable: PickleableExecutable) -> None:
        path = self._get_data_path(node)
        logger.debug(f"Saving executable for node {node.key} to {path}")
        self._fs_client.write(path, dill.dumps(executable, recurse=True))

    def _get_data_path(self, node: PipelineNode) -> str:
        raise NotImplementedError()
        # TODO: make this resilient to failures
        #       when running on a remote pod, we can use the pod name in the path
        #       we can have the driver record the pod name and determine this path
        #       downstream pods can be given the paths to the data they need
        # session_id = self._session_context.get_context().session_id()
        # return f"/oneml-executables/session.{session_id}/{node.key.lstrip('/')}.pkl"
