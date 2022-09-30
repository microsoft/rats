# type: ignore
# flake8: noqa
from .base_dag import NodeName
from .dag_flattener import DAGFlattener
from .flat_dag import FlatDAG
from .processor import Processor
from .run_in_subprocess import RunInSubProcess
from .run_in_subprocess_marker import RunInSubProcessMarker


class AssignProcessorsToComputeUsingMarkers:
    def __init__(self, dag_flattener: DAGFlattener):
        self._dag_flattener = dag_flattener

    def _wrap(self, process_id: str, processor: Processor) -> Processor:
        return RunInSubProcess(process_id, processor)

    def __call__(self, flat_dag: FlatDAG) -> FlatDAG:
        nodes_to_wrap = set()
        cluster_names = set()
        node_to_cluster = dict()
        for node_name in flat_dag.nodes.keys():
            cluster_name = RunInSubProcessMarker.get_process_cluster(node_name)
            if cluster_name is not None:
                if len(cluster_name) < len(node_name):
                    rest_of_name = NodeName(node_name[len(cluster_name) + 1 :])
                    node_to_cluster[node_name] = cluster_name, rest_of_name
                    cluster_names.add(cluster_name)
                nodes_to_wrap.add(cluster_name)
        clustered_dag = self._dag_flattener.break_to_clusters(flat_dag, node_to_cluster)
        for cluster_name in cluster_names:
            clustered_dag.nodes[cluster_name] = self._dag_flattener.unflatten(
                clustered_dag.nodes[cluster_name]
            )
        for node_name in nodes_to_wrap:
            process_id = node_name.split("_")[-1]
            clustered_dag.nodes[node_name] = self._wrap(process_id, clustered_dag.nodes[node_name])
        return FlatDAG(
            nodes=clustered_dag.nodes,
            input_edges=clustered_dag.input_edges,
            edges=clustered_dag.edges,
            output_edges=clustered_dag.output_edges,
        )
