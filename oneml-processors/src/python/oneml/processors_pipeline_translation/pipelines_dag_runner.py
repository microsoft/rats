import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Sequence, Set, Tuple, Union
from xml.etree.ElementTree import PI

from munch import munchify

from oneml.pipelines import (
    IExecutable,
    MlPipelineConfig,
    MlPipelineProvider,
    NullPipeline,
    PipelineNode,
    PipelineSession,
    StorageClient,
    StorageItem,
    StorageItemKey,
)
from oneml.processors import (
    DAGRunner,
    FlatDAG,
    InputPortName,
    NodeName,
    OutputPortAddress,
    OutputPortName,
    Processor,
    RunContext,
)

from .executable_wrapping_processor import ExecutableWrappingProcessingNode

logger = logging.getLogger(__name__)


@dataclass
class ExecutablesDAG:
    nodes: Dict[PipelineNode, ExecutableWrappingProcessingNode]
    dependencies: Dict[PipelineNode, Tuple[PipelineNode, ...]]


class FlatDAGToExecutablesDAG:
    def __init__(
        self,
        storage: StorageClient,
        flat_dag: FlatDAG,
        run_context: RunContext,
    ):
        self.flat_dag = flat_dag
        self.run_context = run_context
        self.storage = storage
        self._set_input_mappings()
        self._set_nodes()
        self._set_dependencies()

    def _set_input_mappings(self) -> None:
        self.input_mappings: Dict[
            NodeName, Dict[InputPortName, Union[InputPortName, OutputPortAddress]]
        ] = dict()
        for input_port_address, port_name in self.flat_dag.input_edges.items():
            port_d = self.input_mappings.setdefault(input_port_address.node, dict())
            port_d[input_port_address.port] = port_name
        for input_port_address, output_port_address in self.flat_dag.edges.items():
            port_d = self.input_mappings.setdefault(input_port_address.node, dict())
            port_d[input_port_address.port] = output_port_address
        logger.debug("Input mappings: %.", self.input_mappings)

    def get_executable(self, node_name: NodeName) -> ExecutableWrappingProcessingNode:
        node = self.flat_dag.nodes[node_name]
        node_run_context = self.run_context.assign(
            identifier=self.run_context.identifier + node_name
        )
        node_input_mappings = self.input_mappings.get(node_name, {})
        return ExecutableWrappingProcessingNode(
            run_context=node_run_context,
            storage=self.storage,
            input_mappings=node_input_mappings,
            node_key=node_name,
            node=node,
        )

    def _set_nodes(self) -> None:
        self.nodes = {
            PipelineNode(node_name): self.get_executable(node_name)
            for node_name in self.flat_dag.nodes.keys()
        }

    def _set_dependencies(self) -> None:
        node_edges: Dict[NodeName, Set[NodeName]] = dict()
        for input_port_address, output_port_address in self.flat_dag.edges.items():
            s = node_edges.setdefault(input_port_address.node, set())
            s.add(output_port_address.node)
        self.dependencies = {
            PipelineNode(k): tuple((PipelineNode(u) for u in v)) for k, v in node_edges.items()
        }
        logger.debug("Node dependencies: %s.", self.dependencies)

    def get_executables_dag(self) -> ExecutablesDAG:
        return ExecutablesDAG(nodes=self.nodes, dependencies=self.dependencies)


class PipelinesDAGRunner(DAGRunner):
    def _save(self, storage: StorageClient, key: str, value: Any) -> Any:
        storage.publish_storage_item(StorageItem(StorageItemKey(key), value))
        logger.debug("Saved DAG input %s.", key)

    def _save_inputs(self, storage: StorageClient, inputs: Dict[str, Any]) -> None:
        for key, value in inputs.items():
            self._save(storage, key, value)

    def _load(self, storage: StorageClient, key: str) -> Any:
        value: Any = storage.get_storage_item(StorageItemKey(key))
        logger.debug("Loaded DAG output %s.", key)
        return value

    def _load_outputs(
        self, storage: StorageClient, flat_dag: FlatDAG
    ) -> Dict[OutputPortName, Any]:
        outputs = munchify(
            {
                key: self._load(storage, flat_dag.output_edges[key])
                for key in flat_dag.get_output_schema().keys()
            }
        )
        return outputs

    def _get_executables_dag(
        self,
        storage: StorageClient,
        flat_dag: FlatDAG,
        run_context: RunContext,
    ) -> ExecutablesDAG:
        converter = FlatDAGToExecutablesDAG(storage, flat_dag, run_context)
        return converter.get_executables_dag()

    def _get_pipeline_session(self, executables_dag: ExecutablesDAG) -> PipelineSession:
        def get_executable_provider(
            node_name: PipelineNode,
        ) -> Callable[[], IExecutable]:
            executable = executables_dag.nodes[node_name]

            def get_executable() -> IExecutable:
                return executable

            return get_executable

        executable_providers = {
            node_name: get_executable_provider(node_name)
            for node_name in executables_dag.nodes.keys()
        }
        dependencies = executables_dag.dependencies

        session = PipelineSession(NullPipeline())
        pipeline_config = MlPipelineConfig(
            session_provider=lambda: session,
            executables_provider=lambda: executable_providers,
            dependencies_provider=lambda: dependencies,
        )
        pipeline_provider = MlPipelineProvider(pipeline_config)
        session.set_pipeline(pipeline_provider.get_pipeline())
        return session

    def run_flattened(
        self, flat_dag: FlatDAG, run_context: RunContext, **inputs: Any
    ) -> Dict[OutputPortName, Any]:

        storage = StorageClient()
        self._save_inputs(storage, inputs)
        executables_dag = self._get_executables_dag(storage, flat_dag, run_context)
        session = self._get_pipeline_session(executables_dag)
        session.run_pipeline()
        outputs = self._load_outputs(storage, flat_dag)
        return outputs
