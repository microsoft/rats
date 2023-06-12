# type: ignore
from collections import ChainMap, defaultdict
from copy import copy
from dataclasses import dataclass
from typing import Any, TypedDict

from oneml.pipelines.dag import PipelineNode, PipelinePort
from ._load_fitted_parameter import LoadFittedParameter
from ._train_and_eval import TrainAndEvalBuilders
from ..dag import DAG, DagNode
from ..services import OnemlProcessorServices
from ..utils import frozendict
from ..ux import OutEntry, Pipeline, PipelineBuilder


@dataclass
class FittedParameterSourceInformation:
    node: DagNode
    port_name: str


class PersistFittedEvalPipeline:
    def __init__(self, type_to_io_manager_mapping: "DefaultDataTypeIOManagerMapper"):
        self._type_to_io_manager_mapping = type_to_io_manager_mapping

    def _with_persisted_fitted_outputs(
        self,
        train_pl: Pipeline
    ) -> Pipeline:
        ports_producing_fitted = {
            tuple(entry)[0]
            for entry in train_pl.out_collections.fitted.values()
        }
        nodes_producing_fitted = defaultdict[DagNode, list[str]](list)
        for port in ports_producing_fitted:
            node = port.node
            port_name = port.param.name
            nodes_producing_fitted[node].append(port_name)
        
        new_nodes = dict(train_pl._dag.nodes)
        for node, port_names in nodes_producing_fitted.items():
            node_props = train_pl._dag.nodes[node]
            new_io_managers = dict(node_props.io_managers)
            for port_name in port_names:
                new_io_managers[port_name] = self._type_to_io_manager_mapping[node_props.outputs[port_name].annotation]
            new_node_props = copy(node_props)
            object.__setattr__(new_node_props, "io_managers", frozendict(new_io_managers))
            new_nodes[node] = new_node_props

        new_dag = DAG(
            nodes=frozendict(new_nodes),
            dependencies=train_pl._dag.dependencies,
        )

        return Pipeline(
            name=train_pl.name,
            dag=new_dag,
            inputs=train_pl.inputs,
            outputs=train_pl.outputs,
            in_collections=train_pl.in_collections,
            out_collections=train_pl.out_collections,
            config=train_pl._config,  # TODO: the config should reflect the new io managers
        )

    def _get_source_info_for_fitted_parameter(self, dag: DAG, entry: OutEntry) -> FittedParameterSourceInformation:
        source = tuple(entry)[0]
        node = source.node
        port_name = source.param.name
        props = dag.nodes[node]
        io_manager_id = props.io_managers[port_name]
        return FittedParameterSourceInformation(
                node=tuple(entry)[0].node,
                port_name=tuple(entry)[0].param.name,
                io_manager_id=io_manager_id,
            )

    def with_persistance(
        self,
        pipeline: Pipeline,
    ) -> Pipeline:
        train_pl, eval_pl = TrainAndEvalBuilders.split_pipeline(pipeline)
        train_pl = self._with_persisted_fitted_outputs(train_pl)
        fitted_parameter_infos = {
            entry_name: self._get_source_info_for_fitted_parameter(train_pl._dag, entry)
            for entry_name, entry in train_pl.out_collections.fitted.items()
        }
        create_fitted_eval_pipeline = PipelineBuilder.task(
            name="create_fitted_eval_pipeline",
            processor_type=CreateFittedEvalPipelineProcessor,
            config=dict(
                my_original_node_name="create_fitted_eval_pipeline",
                eval_pl=eval_pl,
                fitted_parameters=fitted_parameter_infos,
            ),
            services=dict(
                session_id=OnemlProcessorServices.SessionId,
                my_current_node_key=OnemlProcessorServices.GetActiveNodeKey,
            ),
        )
        # Note: we need to specify outputs because there's a bug in the way PipelineBuilder.combine
        # builds the default outputs.
        # See oneml_test.processors.test_pipeline_userio.test_combine_outputs.
        p = PipelineBuilder.combine(
            name=pipeline.name,
            pipelines=[train_pl, eval_pl, create_fitted_eval_pipeline],
            dependencies=(
                train_pl.out_collections.fitted >> eval_pl.in_collections.fitted,
            ),
            outputs=ChainMap(
                {name: train_pl.outputs[name] for name in train_pl.outputs},
                {
                    f"{col_name}.{entry_name}": train_pl.out_collections[col_name][entry_name]
                    for col_name in train_pl.out_collections
                    if col_name != "fitted"
                    for entry_name in train_pl.out_collections[col_name]
                },
                {name: eval_pl.outputs[name] for name in eval_pl.outputs},
                {
                    f"{col_name}.{entry_name}": eval_pl.out_collections[col_name][entry_name]
                    for col_name in eval_pl.out_collections
                    for entry_name in eval_pl.out_collections[col_name]
                },
                {
                    "fitted_eval_pipeline": create_fitted_eval_pipeline.outputs.fitted_eval_pipeline
                }
            ),
        )
        return p


CreateFittedEvalPipelineProcessorOutputs = TypedDict(
    "CreateFittedEvalPipelineProcessorOutputs", {"fitted_eval_pipeline": Pipeline})


class CreateFittedEvalPipelineProcessor:
    """A processor that attached LoadPersisted nodes to an eval pipeline."""

    def __init__(
            self,
            my_original_node_name: str,
            eval_pl: Pipeline,
            fitted_parameters: dict[str, FittedParameterSourceInformation],
            session_id: str,
            my_current_node_key: str
    ):
        my_original_node_key = PipelineNode(str(DagNode(my_original_node_name))).key
        if not my_current_node_key.endswith(my_original_node_key):
            raise ValueError(
                f"Expected my_current_node_key to end with {my_original_node_key}, but got {my_current_node_key}")
        self._node_key_prefix = my_current_node_key[:-len(my_original_node_key)]
        self._eval_pl = eval_pl
        self._fitted_parameters = fitted_parameters
        self._session_id = session_id

    def _get_loader_node(self, fitted_parameter_name: str) -> Pipeline:
        source_info = self._fitted_parameters[fitted_parameter_name]
        original_node_key = PipelineNode(str(source_info.node)).key
        node_key = self._node_key_prefix + original_node_key
        node = PipelineNode(node_key)
        return PipelineBuilder.task(
            name=fitted_parameter_name,
            processor_type=LoadFittedParameter,
            config=dict(
                session_id=self._session_id,
                node=node,
                port=PipelinePort[Any](source_info.port_name),
                iomanager_id=source_info.io_manager_id,
            ),
            services=dict(
                iomanager_registry=OnemlProcessorServices.IOManagerRegistry,
            )
        )

    def process(self) -> CreateFittedEvalPipelineProcessorOutputs:
        loader_nodes = [
            self._get_loader_node(fitted_param_name)
            for fitted_param_name in self._fitted_parameters
        ]
        p = PipelineBuilder.combine(
            name="fitted",
            pipelines=loader_nodes + [self._eval_pl],
            dependencies=tuple(
                loader_node.outputs.data >> self._eval_pl.in_collections.fitted[loader_node.name]
                for loader_node in loader_nodes
            )
        )
        return dict(fitted_eval_pipeline=p)
