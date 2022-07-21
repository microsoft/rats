import base64
import uuid
from typing import Optional

from .base_dag import NodeName
from .dag import DAG
from .identifiers import _level_separator
from .processor import Processor


class RunInSubProcessMarker(DAG):
    """Wraps a part of a DAG to indicate that nodes in that part can be run in a different process.

    This is a placeholder solution until we have a mechanism that optimizes assignment of processor
    nodes to compute nodes.
    """

    def __init__(self, wrapped_processor: Processor):
        process_cluster_id = base64.b32encode(uuid.uuid4().bytes).decode("UTF-8")[:8].lower()
        node_key = f"process_cluster_{process_cluster_id}"
        nodes = {node_key: wrapped_processor}
        input_edges = {
            f"{node_key}.{port_name}": port_name
            for port_name in wrapped_processor.get_input_schema().keys()
        }
        edges = {}
        output_edges = {
            port_name: f"{node_key}.{port_name}"
            for port_name in wrapped_processor.get_output_schema().keys()
        }
        super().__init__(
            nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges
        )

    @classmethod
    def is_marker_level(cls, level: str) -> bool:
        if level.startswith("process_cluster_"):
            rest = level[len("process_cluster_") :]
            if "_" not in rest:
                return True
        return False

    @classmethod
    def get_process_cluster(cls, node_name: NodeName) -> Optional[NodeName]:
        levels = node_name.split(_level_separator)
        process_cluster = None
        for i, level in enumerate(levels):
            if cls.is_marker_level(level):
                process_cluster = NodeName(_level_separator.join(levels[: (i + 1)]))
        return process_cluster
