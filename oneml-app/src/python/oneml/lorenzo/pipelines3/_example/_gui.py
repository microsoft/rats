import io

import cairosvg
import pydot
import pygame

from oneml.pipelines import (
    PipelineNodeState,
    ILocatePipelineNodes,
    ILocatePipelineNodeDependencies,
    ILocatePipelineNodeState,
)

state_colors_map = {
    PipelineNodeState.REGISTERED: "/dark27/3",
    PipelineNodeState.QUEUED: "/dark27/6",
    PipelineNodeState.PENDING: "/dark27/2",
    PipelineNodeState.RUNNING: "/dark27/1",
    PipelineNodeState.COMPLETED: "/dark27/5",
    PipelineNodeState.FAILED: "/dark27/4",
}


class DotDag:
    _node_client: ILocatePipelineNodes
    _dependencies_client: ILocatePipelineNodeDependencies
    _node_state_client: ILocatePipelineNodeState

    def __init__(
            self,
            node_client: ILocatePipelineNodes,
            dependencies_client: ILocatePipelineNodeDependencies,
            node_state_client: ILocatePipelineNodeState):
        self._node_client = node_client
        self._dependencies_client = dependencies_client
        self._node_state_client = node_state_client

    def graph(self) -> pydot.Dot:
        graph = pydot.Dot("DAG", graph_type="digraph")

        for node in self._node_client.get_nodes():
            node_state = self._node_state_client.get_node_state(node)
            graph.add_node(pydot.Node(
                name=f'"{node.key}"',
                shape="box",
                style="filled",
                fillcolor=state_colors_map[node_state]))

            for dep in self._dependencies_client.get_node_dependencies(node):
                graph.add_edge(pydot.Edge(f'"{dep.key}"', f'"{node.key}"'))

        return graph


class DagSvg:
    _dot_dag: DotDag

    def __init__(self, dot_dag: DotDag):
        self._dot_dag = dot_dag

    def svg(self) -> bytes:
        return self._dot_dag.graph().create(format="svg", prog="dot")


class DagVisualizer:

    _svg_client: DagSvg

    def __init__(self, svg_client: DagSvg):
        self._svg_client = svg_client

    def execute(self) -> None:
        pygame.init()
        pygame.font.init()
        monitor = pygame.display.Info()

        monitor_size = (monitor.current_w, monitor.current_h)
        window = pygame.display.set_mode(monitor_size, pygame.NOFRAME)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.display.quit()
                    return
                if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                    pygame.display.quit()
                    return

            # Use SVG so we can maintain high resolution
            svg = self._svg_client.svg()
            # binary data representing the png of the DAG so that pygame can render it
            png = cairosvg.svg2png(
                bytestring=svg,
                output_width=window.get_width(),
                output_height=window.get_height(),
                dpi=300,
                background_color="black",
            )
            # Create a file-like object for the png data
            data = io.BytesIO(png)
            # Create a pygame Surface object for rendering the DAG to our window
            dag_surface = pygame.image.load(data)

            window.blit(dag_surface, (0, 0))
            pygame.display.update()
