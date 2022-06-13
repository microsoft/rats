from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Tuple, Type

from oneml.lorenzo.pipelines._dag_client import ConcurrentDagNode

from ._mira import LoadMiraTask, LoadMiraTaskFactory, LoadMiraTaskPresenter, Mira
from ._repertoire import (
    LoadRepertoireTask,
    LoadRepertoireTaskFactory,
    LoadRepertoireTaskPresenter,
    Repertoire,
    RepertoireLabels,
)
from ._stats import SampleStatsTask, SampleStatsTaskFactory, SampleStatsTaskPresenter


class FakeTask:
    def execute(self) -> None:
        print("FAKE TASK!")


class DagMapper:
    _data: Dict[Tuple[str, ...], Callable[[], None]]

    def __init__(self, data: Dict[Tuple[str, ...], Callable[[], None]]):
        self._data = data

    def get_by_input(self, input_names: Tuple[str, ...]) -> Callable[[], None]:
        return self._data.get(input_names, self._no_op)

    def _no_op(self) -> None:
        print("INPUT MISS!")


class ExamplePipeline(
        LoadMiraTaskPresenter, LoadRepertoireTaskPresenter, SampleStatsTaskPresenter):

    _completed_tasks: List[str]
    _dag_mapper: DagMapper

    _mira: Optional[Mira]
    _repertoire: Optional[Repertoire]

    def __init__(self):
        self._completed_tasks = []
        self._dag_mapper = DagMapper({
            tuple([]): self._load_data,
            tuple(["repertoire", "mira"]): self._run_stats,
        })

    def _load_data(self) -> None:
        repertoire_task = LoadRepertoireTask(presenter=self, seed="abcd")
        mira_task = LoadMiraTask(presenter=self, seed="abcd")

        ConcurrentDagNode({
            "repertoire": repertoire_task,
            "mira": mira_task,
        }).execute()

    def _run_stats(self) -> None:
        SampleStatsTask(presenter=self, repertoire=self._repertoire, mira=self._mira).execute()

    def on_mira_ready(self, miras: Mira) -> None:
        self._mira = miras
        self._completed_tasks.append("mira")
        print(self._completed_tasks)

        self.execute()

    def on_repertoire_ready(self, repertoires: Repertoire) -> None:
        self._repertoire = repertoires
        self._completed_tasks.append("repertoire")
        print(self._completed_tasks)

        self.execute()

    def on_stats_ready(self, total_samples: int) -> None:
        print(f"STATS! {total_samples} TOTAL SAMPLES!")

    def execute(self) -> None:
        self._dag_mapper.get_by_input(tuple(self._completed_tasks))()

##############################################


class PipelineNode(ABC):
    @abstractmethod
    def execute_node(self) -> None:
        pass


class PipelineNodeProvider(ABC):
    @abstractmethod
    def get_node(self) -> PipelineNode:
        pass


class Pipeline(ABC):
    @abstractmethod
    def execute_pipeline(self) -> None:
        pass


class PipelineProvider(ABC):
    @abstractmethod
    def get_pipeline(self) -> Pipeline:
        pass


class DagRegistry:

    _nodes: Dict[Type, PipelineNodeProvider]
    _edges: Dict[Type, Tuple[Type, ...]]

    def __init__(self):
        self._nodes = {}
        self._edges = {}

    def register_node(self, key: Type, value: PipelineNodeProvider) -> None:
        if key in self._nodes:
            raise RuntimeError(f"Node already registered: {key}")

        self._nodes[key] = value

    def register_edges(self, key: Type, inputs: Tuple[Type, ...]) -> None:
        if key in self._edges:
            raise RuntimeError(f"Node edges already registered: {key}")

        self._edges[key] = inputs

    def get_schedulable_nodes(
            self,
            available_edges: Tuple[Type, ...]) -> Tuple[PipelineNodeProvider, ...]:
        result = []
        for node, input_edges in self._edges.items():
            if set(input_edges).issubset(available_edges):
                result.append(self._nodes[node])

        return tuple(result)



class PipelineRegistry:

    _pipelines: Dict[Type, PipelineProvider]

    def __init__(self):
        self._pipelines = {}

    def register_pipeline(self, key: Type, value: PipelineProvider) -> None:
        if key in self._pipelines:
            raise RuntimeError(f"Duplicate pipeline: {key}")

        self._pipelines[key] = value

    def execute(self, key) -> None:
        if key not in self._pipelines:
            raise RuntimeError(f"Pipeline not found: {key}")

        """
        maybe the pipeline registry is a list of providers instead of pipelines?
        pipeline_provider.build()
        `.build()` can return an executable pipeline that has already registered edges/nodes?
        """
        pipeline = self._pipelines[key].get_pipeline()
        pipeline.execute_pipeline()


class ExamplePipeline2(Pipeline, PipelineProvider, PipelineNode, PipelineNodeProvider):

    _dag: DagRegistry

    def main(self) -> None:
        pipeline_registry = PipelineRegistry()
        pipeline_registry.register_pipeline(ExamplePipeline2, self)
        pipeline_registry.execute(ExamplePipeline2)

    def get_pipeline(self) -> Pipeline:
        dag = DagRegistry()

        step1ref = type("step-1", tuple([ExamplePipeline2]), {})
        step2ref = type("step-2", tuple([ExamplePipeline2]), {})

        dag.register_node(step1ref, self)
        dag.register_node(step2ref, self)

        dag.register_edges(step1ref, tuple([step2ref]))
        dag.register_edges(step2ref, tuple([]))

        self._dag = dag
        return self

    def get_node(self) -> PipelineNode:
        return self

    def execute_pipeline(self) -> None:
        print("executing pipeline")
        for node in self._dag.get_schedulable_nodes(tuple([])):
            node.get_node().execute_node()
        """
        - find nodes we can execute
        - run them in parallel
        - listen for nodes completing
        - repeat
        """

    def execute_node(self) -> None:
        print("executing node")

######################################################


class DataVal(LoadRepertoireTaskPresenter):

    def on_repertoire_ready(self, repertoires: Repertoire) -> None:
        assert repertoires.count() > 0

    def on_labels_ready(self, labels: RepertoireLabels) -> None:
        assert labels.count() > 0


class DataVal2(LoadRepertoireTaskPresenter, LoadMiraTaskPresenter):

    rep: Repertoire
    labels: RepertoireLabels
    miras: Mira

    def on_repertoire_ready(self, repertoires: Repertoire) -> None:
        self.rep = repertoires

    def on_labels_ready(self, labels: RepertoireLabels) -> None:
        self.labels = labels

    def on_mira_ready(self, miras: Mira) -> None:
        self.miras = miras


def test_thing():
    presenter = DataVal()
    task = LoadRepertoireTask(presenter=presenter, seed="abcd")
    task.execute()

    presenter2 = DataVal2()
    LoadRepertoireTask(presenter=presenter2, seed="abcd").execute()
    LoadMiraTask(presenter=presenter2, seed="abcd").execute()
    assert isinstance(presenter2.rep, Repertoire)
    assert isinstance(presenter2.labels, RepertoireLabels)
    assert isinstance(presenter2.miras, Mira)
