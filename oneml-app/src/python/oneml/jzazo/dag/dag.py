from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

from oneml.lorenzo.pipelines import PipelineStep

TaskName = str


@dataclass
class Resources:
    min_cpu: int = 1
    min_mem: str = "4Gi"
    max_cpu: Optional[int] = None
    max_mem: Optional[str] = None
    gpus: Optional[int] = None


class Task:
    name: TaskName
    step: Optional[PipelineStep]
    resources: Optional[Resources]

    _dependencies: Set[str]
    _conditions: Optional[List[Callable[..., bool]]]

    def __init__(
        self,
        name: TaskName,
        step: Optional[PipelineStep],
        resources: Optional[Resources],
        conditions: Optional[List[Callable[[], bool]]] = None,
    ) -> None:
        self.name = name
        self.step = step
        self.resources = resources
        self._dependencies = set()
        self._conditions = conditions

    def add_dependency(self, dependency: TaskName) -> None:
        return self._dependencies.add(dependency)

    def run(self) -> None:
        pass

    @property
    def dependencies(self) -> Set[str]:
        return self._dependencies

    @property
    def conditions(self) -> bool:
        return all(condition() for condition in self._conditions) if self._conditions else True


class DAG(Task):

    _nodes: Dict[TaskName, Task]
    _edges: Set[Tuple[TaskName, TaskName]]

    def __init__(
        self,
        name: TaskName,
        nodes: Dict[TaskName, Task],
        edges: Set[Tuple[TaskName, TaskName]],
        resources: Resources,
    ) -> None:
        assert all(task_name == task.name for task_name, task in nodes.items())
        assert len(edges) == len(set(edges))
        super().__init__(name=name, step=None, resources=resources)
        self._nodes = nodes
        self._edges = edges

        for task, other in edges:
            self._add_dependency(task, other)  # task does not need to belong to the dag

        self._dependencies = set(nodes.keys())  # dag depends on all dag.nodes

    def _add_dependency(self, task: TaskName, other: TaskName) -> None:
        self.get_node(other).add_dependency(task)

    @property
    def nodes(self) -> Dict[TaskName, Task]:
        return self._nodes

    @property
    def edges(self) -> Set[Tuple[TaskName, TaskName]]:
        return self._edges

    def add_node(self, node: Task) -> None:
        assert node.name not in self.nodes.keys()
        self._nodes[node.name] = node

    def add_edge(self, edge: Tuple[TaskName, TaskName]) -> None:
        self._edges.add(edge)
        self._add_dependency(*edge)

    def get_node(self, name: str) -> Task:
        return self._nodes[name]


class DAGRunner:

    dag: DAG

    _nodes: Dict[TaskName, Task]
    _injections: Dict[TaskName, List[TaskName]]  # downstream tasks

    def __init__(self, dag: DAG) -> None:
        self.dag = dag
        self._nodes = self._infer_nodes(dag)
        self._injections = self._infer_injections()
        self._validate()

    def _infer_nodes(self, dag: DAG) -> Dict[TaskName, Task]:
        nodes: Dict[TaskName, Task] = {}
        visited = set()
        queue = deque((name, task) for name, task in dag.nodes.items())
        while queue:
            name, task = queue.pop()  # breadth-first
            nodes[name] = task
            if isinstance(task, DAG):
                queue.extend([(n, t) for n, t in dag.nodes.items() if t not in visited])
            visited.add(name)
        return nodes

    def _infer_injections(self) -> Dict[TaskName, List[TaskName]]:
        injections: Dict[TaskName, List[TaskName]] = defaultdict(list)
        for name, task in self._nodes.items():
            for dependency in task.dependencies:
                injections[dependency].append(name)
        return injections

    def _validate(self) -> None:
        pass

    def get_node(self, name: TaskName) -> Task:
        return self._nodes[name]

    def run(self) -> None:
        pending = deque(self._nodes.keys())
        completed: Set[TaskName] = set()
        removed: Set[TaskName] = set()

        while pending:
            name = pending.popleft()
            if name in completed or name in removed:
                continue

            task = self.get_node(name)
            if task.dependencies <= completed:
                if task.conditions:
                    task.run()
                    completed.add(name)
                    pending.extendleft(self._injections[name])
                else:
                    removed |= self._branch_tasks(name)

    def _branch_tasks(self, name: TaskName) -> Set[TaskName]:
        branch_tasks = set()
        injections = deque([name])
        while injections:
            downstream = injections.popleft()
            branch_tasks.add(downstream)
            injections.extend(self._injections[downstream])
        return branch_tasks
