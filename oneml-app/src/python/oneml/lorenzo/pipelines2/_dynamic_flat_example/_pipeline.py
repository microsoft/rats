from typing import Type

from oneml.lorenzo.pipelines import InMemoryStorage, OutputType, PipelineDataWriter, PipelineOutput
from oneml.lorenzo.pipelines2 import (
    IPipeline,
    IProvidePipelines,
    PipelineNodeDag,
    PipelineNodeDagBuilder,
)

from ._load_mira import LoadMiraNode, LoadMiraNodeProvider, Mira
from ._load_repertoire import (
    LoadRepertoireNode,
    LoadRepertoireNodeProvider,
    Repertoire,
    RepertoireLabels,
)
from ._stats import SampleStatsNode, SampleStatsNodeProvider


class MyPipelineOutput(PipelineOutput):

    _storage: PipelineDataWriter

    def __init__(self, storage: PipelineDataWriter):
        self._storage = storage

    def add(self, name: Type[OutputType], value: OutputType) -> None:
        print(f"ADDING OUTPUT: {name}")
        self._storage.save(name, value)

    def on_repertoire_ready(self, repertoires: Repertoire) -> None:
        print("REPERTOIRE DATA READY!")
        self._storage.save(Repertoire, repertoires)

    def on_labels_ready(self, labels: RepertoireLabels) -> None:
        print("REPERTOIRE LABELS READY!")
        self._storage.save(RepertoireLabels, labels)

    def on_mira_ready(self, miras: Mira) -> None:
        print("MIRA DATA READY!")
        self._storage.save(Mira, miras)

    def on_stats_ready(self, total_samples: int) -> None:
        print("STATS READY!")
        self._storage.save(int, total_samples)

    def pre_node_execution(self, key, value) -> None:
        print(f"pre exec: {key}, {value}")


class MyPipeline(IPipeline):

    _output_client: MyPipelineOutput
    _dag: PipelineNodeDag

    def __init__(self, output_client: MyPipelineOutput, dag: PipelineNodeDag):
        self._output_client = output_client
        self._dag = dag

    def execute_pipeline(self) -> None:
        print("EXECUTING PIPELINE")
        for key, provider in self._dag.get_items():
            # self._presenter.pre_node_execution(key, provider)
            provider.get_pipeline_node().execute_node()


class MyPipelineProvider(IProvidePipelines[MyPipeline]):

    _dag_builder: PipelineNodeDagBuilder

    def __init__(self, dag_builder: PipelineNodeDagBuilder):
        self._dag_builder = dag_builder

    def get_pipeline(self) -> MyPipeline:
        """
        - You can register edges to nodes that are represented by extenal datasets.
        - A provider of a node handles internal/external differences.
        """
        storage = InMemoryStorage()

        pipeline_output = MyPipelineOutput(storage=storage)

        load_repertoire_node = LoadRepertoireNodeProvider(output_client=pipeline_output)
        load_mira_node = LoadMiraNodeProvider(output_client=pipeline_output)
        stats_node = SampleStatsNodeProvider(output_client=pipeline_output, storage=storage)

        self._dag_builder.register_node(SampleStatsNode, stats_node)
        self._dag_builder.register_node(LoadRepertoireNode, load_repertoire_node)
        """
        self._dag_builder.register_node(NormalizeRepertoireNode, normalize_repertoire_node)
        """
        self._dag_builder.register_node(LoadMiraNode, load_mira_node)

        # [LoadRepertoireNode, LoadMiraNode] -> SampleStatsNode
        self._dag_builder.register_edges(SampleStatsNode, (LoadRepertoireNode, LoadMiraNode))
        """
        self._dag_builder.register_node(NormalizeRepertoireNode, normalize_repertoire_node)
        """

        """
        - Need to refine how data moves between nodes
        - Steps define dependencies to data
        - Data dependencies define compute DAG edges
        """

        """
        - What if we make a Node data structure?
        Node:
            outputs: Tuple[UniqueDataKey, ...]
            inputs: Tuple[UniqueDataKey, ...]
        - Do we want to be able to detect when a node fails to persist an output?
        """

        return MyPipeline(output_client=pipeline_output, dag=self._dag_builder.build())


class DockerBuildNode:

    def execute(self) -> None:
        """
        subprocess.run(["docker", "build"])
        """


"""
class Predictor:
    _samples
    _model

    def execute():
        predictions = self._model.predict(self._samples)

prediction_pipeline.run(samples1)
    - load pipeline template
    - render template with samples1
    - run pipeline
prediction_pipeline.run(samples2)
    - build pipeline
    - run pipeline
"""

"""
- What if the DAG is a queue instead?
- A data structure where the key is the edges (gates? conditions?) and values are all steps needing to run?
- As outputs become available, we mark all the keys that are satisfied
- We keep a queue of "runnable" nodes
- When a new node gets added to the DAG, we add it to the data structure
- If edges are already resolved, we schedule it as runnable
"""

"""
Is this a "game loop"?
- continue until pipeline is complete
- update registry of completed tasks
- 

Is each node a FSM?
- submitted
- pending (waiting for inputs)
- queued (waiting for running)
- running
- completed
"""
