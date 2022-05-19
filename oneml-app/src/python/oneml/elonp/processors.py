import logging

from dataclasses import dataclass

import inspect
import numpy as np
import numpy.typing as npt
from typing_extensions import TypedDict
from typing import Type, Dict, Any, Protocol, runtime_checkable, Sequence, Tuple, List, Union
from networkx import DiGraph
from networkx.algorithms.dag import topological_sort
from collections import defaultdict
import sklearn.linear_model

logger = logging.getLogger(__name__)

@runtime_checkable
class Processor(Protocol):
    def get_input_schema(self) -> Dict[str, Type]:
        ...

    def get_output_schema(self) -> Dict[str, Type]:
        ...

    def process(self, **kwds: Any) -> Dict:
        ...


@runtime_checkable
class ProcessingFunc(Protocol):
    def process(self, **kwds: Any) -> Dict:
        ...


def processor_from_func(processing_func_class: Type[ProcessingFunc]) -> Type[Processor]:
    signature = inspect.signature(processing_func_class.process)
    
    def get_input_schema(self) -> Dict[str, Type]:    
        parameters = list(signature.parameters.items())[1:]
        return {
            param_name: parameter.annotation
            for (param_name, parameter) in parameters
        }

    def get_output_schema(self) -> Dict[str, Type]:
        return_annotation: TypedDict = signature.return_annotation.__annotations__
        return {
            param_name: param_type
            for param_name, param_type in return_annotation.items()
        }

    processing_func_class.get_input_schema = get_input_schema
    processing_func_class.get_output_schema = get_output_schema
    
    return processing_func_class


@processor_from_func
@dataclass
class FittedStandardizer:
    # parameters
    offset: float
    scale: float

    def process(self, features: npt.ArrayLike) -> TypedDict("FittedStandardizerOutput", {"features": npt.ArrayLike}):
        features = (features + self.offset) * self.scale
        return dict(
            features=features
        )


@processor_from_func
@dataclass
class Standardizer(ProcessingFunc):
    def process(self, features: npt.ArrayLike) -> TypedDict("StandardizerOutput", {"fitted": FittedStandardizer, "features": npt.ArrayLike}):
        offset = -features.mean(axis=0)
        scale = 1. / features.std(axis=0)
        f = FittedStandardizer(offset=offset, scale=scale)
        features = f.process(features)["features"]
        return dict(
            fitted=f,
            features=features
        )


@processor_from_func
@dataclass
class FittedLogisticRegression:
    classes: npt.ArrayLike
    coef: npt.ArrayLike
    intercept: npt.ArrayLike

    def process(self, features: npt.ArrayLike) -> TypedDict("FittedLogisticRegressionOutput", {"predictions": npt.ArrayLike}):
        lr = sklearn.linear_model.LogisticRegression()
        lr.classes_ = self.classes
        lr.coef_ = self.coef
        lr.intercept_ = self.intercept
        predictions = lr.predict(X=features)
        return dict(
            predictions=predictions
        )


@processor_from_func
class LogisticRegression(ProcessingFunc):
    def process(self, features: npt.ArrayLike, labels:npt.ArrayLike) -> TypedDict("LogisticRegressionOutput", {
        "fitted": FittedLogisticRegression, "predictions": npt.ArrayLike}):
        lr = sklearn.linear_model.LogisticRegression()
        lr.fit(
            X=features,
            y=labels,
        )
        fitted = FittedLogisticRegression(
            classes = lr.classes_,
            coef = lr.coef_,
            intercept = lr.intercept_
        )
        predictions = fitted.process(features)
        return dict(
            fitted=fitted,
            predictions=predictions
        )


@dataclass
class DAG(Processor):
    nodes: Dict[str, Processor]
    edges: Sequence[Tuple[Tuple[str, str], Tuple[str, str]]]
    inputs: Sequence[Tuple[str, Tuple[str, str]]]
    outputs: Sequence[Tuple[str, Tuple[str, str]]]

    def get_input_schema(self) -> Dict[str, Type]:
        return {
            export_name: self.nodes[node_name].get_input_schema()[input_name_in_node]
            for export_name, (node_name, input_name_in_node) in self.inputs
        }

    def get_output_schema(self) -> Dict[str, Type]:
        return {
            export_name: self.nodes[node_name].get_output_schema()[output_name_in_node]
            for export_name, (node_name, output_name_in_node) in self.outputs
        }

    def _get_mapping_from_node_output_names(self) -> Dict[Tuple[str, str], List[Union[str, Tuple[str, str]]]]:
        d = defaultdict(list)
        for ((source_node_name, output_name_in_source), (target_node_name, input_name_in_target)) in self.edges:
            d[(source_node_name, output_name_in_source)].append((target_node_name, input_name_in_target))
        for export_name, (node_name, output_name_in_node) in self.outputs:
            d[(node_name, output_name_in_node)].append(export_name)
        return d

    def _get_node_edges(self) -> Sequence[Tuple[str, str]]:
        edges = [
            ("***source***", target_node_name)
            for _, (target_node_name, input_name_in_target) in self.inputs
        ] + [
            (source_node_name, target_node_name)
            for ((source_node_name, output_name_in_source), (target_node_name, input_name_in_target)) in self.edges
        ] + [
            (source_node_name, "***target***")
            for _, (source_node_name, output_name_in_source) in self.outputs
        ]
        return list(set(edges))

    def _get_digraph(self) -> DiGraph:
        return DiGraph(self._get_node_edges())

    def _get_processing_order(self) -> Sequence[str]:
        g = self._get_digraph()
        return list(topological_sort(g))[1:-1]

    def process(self, **kwds: Any) -> Dict[str, Type]:
        edges_dict = self._get_mapping_from_node_output_names()
        data_dict = dict()
        for export_name, (node_name, input_name_in_node) in self.inputs:
            logger.debug("adding data for %s", (node_name, input_name_in_node))
            data_dict[(node_name, input_name_in_node)] = kwds[export_name]
        for node_name in self._get_processing_order():
            logger.debug("calling %s", node_name)
            node = self.nodes[node_name]
            node_inputs = {
                input_name_in_node: data_dict[(node_name, input_name_in_node)]
                for input_name_in_node in node.get_input_schema().keys()
            }
            node_outputs = node.process(**node_inputs)
            for output_name_in_node, output_value in node_outputs.items():
                targets = edges_dict[(node_name, output_name_in_node)]
                for target in targets:
                    logger.debug("adding data for %s", target)
                    data_dict[target] = output_value
        export_outputs = {
            export_name: data_dict[export_name]
            for export_name in self.get_output_schema().keys()
        }
        return export_outputs
