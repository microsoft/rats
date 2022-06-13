from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from time import sleep
from typing import Any, Dict, List, Protocol, Set, Tuple, Type


class DagNode(Protocol):
    @abstractmethod
    def execute(self) -> None:
        pass


class DagNodePresenter(ABC):
    @abstractmethod
    def on_completion(self, node: DagNode) -> None:
        """"""

    @abstractmethod
    def on_checkpoint(self, ref: Type[object]) -> None:
        """"""


class DagEdgeRegistry:
    def require(self, node: DagNode, output: Type[object]) -> None:
        pass


class Dag(ABC):
    @abstractmethod
    def execute(self) -> None:
        """"""


class DagRunner:

    _num_threads: int

    def __init__(self, num_threads: int):
        self._num_threads = num_threads

    def submit(self, node: DagNode) -> None:
        self._executor().submit(node.execute)

    @lru_cache()
    def _executor(self) -> ThreadPoolExecutor:
        return ThreadPoolExecutor(max_workers=self._num_threads)


class ConcurrentDag(Dag):
    _nodes: Dict[Any, DagNode]

    def __init__(self, nodes: Dict[Any, DagNode]):
        self._nodes = nodes

    def execute(self) -> None:
        print(f"executing concurrent dag: {self._nodes.keys()}")
        with ThreadPoolExecutor(max_workers=len(self._nodes)) as executor:
            futures: List[Future] = []  # type: ignore
            for node_id, node in self._nodes.items():
                futures.append(executor.submit(self._run_node, node_id, node))

            for future in as_completed(futures):
                # Causes exceptions to propagate if they were thrown in the thread
                future.result()

    def _run_node(self, node_id: str, node: DagNode) -> None:
        print(f"executing node: {node_id}")
        node.execute()
        print(f"done executing node: {node_id}")


class ConcurrentDagNode(ConcurrentDag, DagNode):
    pass


class SequentialDag(Dag):
    _nodes: Tuple[DagNode, ...]

    def __init__(self, nodes: Tuple[DagNode, ...]):
        self._nodes = nodes

    def execute(self) -> None:
        for node in self._nodes:
            node.execute()


class DagBuilder:

    _nodes: List[DagNode]

    def add_node(self, node) -> None:
        self._nodes.append(node)

    def build(self) -> Dag:
        return SequentialDag(tuple(self._nodes))


class DataDrivenDagBuilder:
    _nodes: Tuple[DagNode, ...]

    def __init__(self, nodes: Tuple[DagNode, ...]):
        self._nodes = nodes

    def get(self) -> Dag:
        pass


class TestNode(DagNode):

    _sleep_num: int

    def __init__(self, sleep_num: int):
        self._sleep_num = sleep_num

    def execute(self) -> None:
        sleep(self._sleep_num)


class GuardedDagNode(DagNode, ABC):

    _missing_reqs: Set[Type[object]]
    _node: DagNode

    def __init__(
            self,
            missing_reqs: Set[Type[object]],
            node: DagNode):
        self._missing_reqs = missing_reqs.copy()
        self._node = node

    def toggle(self, req: Type[object]) -> None:
        if req not in self._missing_reqs:
            raise RuntimeError(f"req not found: {req}")

        self._missing_reqs.remove(req)
        if len(self._missing_reqs) == 0:
            self.execute()

    def execute(self) -> None:
        if len(self._missing_reqs) > 0:
            raise RuntimeError(f"missing reqs before node can be executed: {self._missing_reqs}")

        self._node.execute()


class MarkedTaskNode(DagNode, DagNodePresenter):

    _node: DagNode

    def __init__(self, node: DagNode):
        self._node = node

    def execute(self) -> None:
        pass

    def on_completion(self, node: DagNode) -> None:
        pass

    def on_checkpoint(self, ref: Type[object]) -> None:
        pass


def _test() -> None:
    """
    - Every pipeline is a Sequential DAG of Concurrent DAGs.
    - Each node has a single callback that runs another Concurrent DAG.
    - Each Concurrent DAG is a point on the path of all possible requirements
    OR
    - Every pipeline is a Sequential DAG of Concurrent DAGs.
    - Each node is a Sequential DAG of all nodes requiring a unique set of node outputs
    - Each Concurrent DAG is a point on the path of all possible requirements
    """
    pipeline = SequentialDag(tuple([
        ConcurrentDagNode({
            "level-1.node-1": TestNode(3),
            "level-1.node-2": TestNode(2),
            "level-1.node-3": TestNode(1),
        }),
        ConcurrentDagNode({
            "level-2.node-1": TestNode(3),
            "level-2.node-2": TestNode(2),
            "level-2.node-3": TestNode(1),
        }),
        ConcurrentDagNode({
            "level-3.node-1": TestNode(3),
            "level-3.node-2": TestNode(1),
            "level-3.node-3": TestNode(2),
        }),
    ]))
    pipeline.execute()


if __name__ == "__main__":
    _test()

"""
# Always alphabetical
- []
    - [] -> Load[Mira]
    - [] -> Load[Repertoire]
- [Load[Mira]]
    - Load[Mira] -> Clean[Mira]
- [Load[Repertoire]]
    - Load[Repertoire] -> Clean[Repertoire]
- [Clean[Mira]]
    - [Clean[Mira]] -> Count[Mira]
    - [Clean[Mira]] -> Validate[Mira]
- [Clean[Mira], Clean[Repertoire]]  # Gets "pinged" twice; once per req
    - [Clean[Mira], Clean[Repertoire]] -> Train[Params], Train[Fitted]
"""
