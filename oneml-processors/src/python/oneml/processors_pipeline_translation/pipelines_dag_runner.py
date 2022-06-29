import logging
from typing import Any, Callable, Dict, Set, Union

from munch import munchify

from oneml.pipelines import (
    IManageStorageItems,
    LocalDiskStorageClient,
    MlPipelineConfig,
    MlPipelineProvider,
    NullPipeline,
    PipelineNode,
    PipelineSession,
    StorageClient,
    StorageItem,
    StorageItemKey,
)
from oneml.processors import DAG, DAGRunner, InputPortName, NodeName, OutputPortAddress, RunContext
from oneml.processors.processor import OutputPortName, Processor

from .executable_wrapping_processor import ExecutableWrappingProcessingNode

logger = logging.getLogger(__name__)


class PipelinesDAGRunner(DAGRunner):
    def __init__(self, remote_mode: str) -> None:
        self._storage_factory: Callable[[], IManageStorageItems]
        if remote_mode == "thread":
            self._storage_factory = lambda: StorageClient()
        elif remote_mode == "process":
            self._storage_factory = lambda: LocalDiskStorageClient("/tmp")
        else:
            raise ValueError(
                f"remote_mode should be one of <thread, process>. It was: <{remote_mode}>."
            )

    def run(self, dag: DAG, run_context: RunContext, **inputs: Any) -> Dict[OutputPortName, Any]:

        flat_dag = dag._flatten()
        storage = self._storage_factory()

        def get_input_mappings() -> Dict[
            NodeName, Dict[InputPortName, Union[InputPortName, OutputPortAddress]]
        ]:
            d: Dict[
                NodeName, Dict[InputPortName, Union[InputPortName, OutputPortAddress]]
            ] = dict()
            for input_port_address, port_name in flat_dag.input_edges.items():
                port_d = d.setdefault(input_port_address.node, dict())
                port_d[input_port_address.port] = port_name
            for input_port_address, output_port_address in flat_dag.edges.items():
                port_d = d.setdefault(input_port_address.node, dict())
                port_d[input_port_address.port] = output_port_address
            logger.debug("Input mappings: %.", d)
            return d

        def get_node_edges() -> Dict[NodeName, Set[NodeName]]:
            d = dict()
            for input_port_address, output_port_address in flat_dag.edges.items():
                s = d.setdefault(input_port_address.node, set())
                s.add(output_port_address.node)
            logger.debug("Node dependencies: %s.", d)
            return d

        def load(key: str) -> Any:
            value: Any = storage.get_storage_item(StorageItemKey(key))
            logger.debug("Loaded DAG output %s.", key)
            return value

        def save(key: str, value: Any) -> Any:
            storage.publish_storage_item(StorageItem(StorageItemKey(key), value))
            logger.debug("Saved DAG input %s.", key)

        for key, value in inputs.items():
            save(key, value)
        input_mappings = get_input_mappings()
        node_edges = get_node_edges()

        def get_executable_provider(
            node_name: NodeName, node: Processor
        ) -> Callable[[], ExecutableWrappingProcessingNode]:
            node_run_context = run_context.assign(identifier=node_name)
            node_input_mappings = input_mappings.get(node_name, {})
            assert node_input_mappings.keys() == node.get_input_schema().keys()

            def get_executable() -> ExecutableWrappingProcessingNode:
                return ExecutableWrappingProcessingNode(
                    run_context=node_run_context,
                    storage=storage,
                    input_mappings=node_input_mappings,
                    node_key=node_name,
                    node=node,
                )

            return get_executable

        executables = {
            PipelineNode(node_name): get_executable_provider(node_name, node)
            for node_name, node in flat_dag.nodes.items()
        }
        dependencies = {
            PipelineNode(node_name): tuple(
                (PipelineNode(upstream_node_name) for upstream_node_name in upstream_node_names)
            )
            for node_name, upstream_node_names in node_edges.items()
        }

        session = PipelineSession(NullPipeline())
        pipeline_config = MlPipelineConfig(
            session_provider=lambda: session,
            executables_provider=lambda: executables,
            dependencies_provider=lambda: dependencies,
        )
        pipeline_provider = MlPipelineProvider(pipeline_config)
        session.set_pipeline(pipeline_provider.get_pipeline())
        session.run_pipeline()
        outputs = munchify(
            {key: load(flat_dag.output_edges[key]) for key in flat_dag.get_output_schema().keys()}
        )
        return outputs
