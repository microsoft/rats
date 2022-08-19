# type: ignore
# flake8: noqa
import re
from copy import deepcopy
from dataclasses import dataclass
from functools import partial
from inspect import signature
from typing import Any, Dict, List, Pattern, Tuple, Type, Union

from omegaconf import DictConfig

from .processor import Estimator, Processor, Storage, Transformer
from .step import FormatDataloader, ModelTrain, StandardizeTrain


@dataclass
class Nodes:
    standardization: DictConfig = StandardizeTrain
    format_dataloader: Processor = FormatDataloader
    model_train: Processor = ModelTrain


@dataclass
class Inputs:
    standardization: Dict[str, str] = {"X": "input.X"}
    format_dataloader: Dict[str, str] = {"X": "standardization.Z", "Y": "input.Y"}
    model_train: Dict[str, str] = {"dataloader": "format_dataloader.dataloader"}


# @dataclass
# class EvalInputs:
#     standardization_eval: Dict[str, str] = {"X": "input_eval.X"}
#     format_dataloader_eval: Dict[str, str] = {"dataset": "standardization_eval.Z"}
#     model_eval: Dict[str, str] = {"dataloader": "format_dataloader_eval.dataloader"}


# problem when estimator & transformer inputs don't have equal names


class Inputs2Eval:
    pattern: Pattern[str] = re.compile(r"(train)")

    def __init__(self, pattern: Pattern[str] = pattern) -> None:
        self.pattern = pattern

    def _sub_or_append_eval_to_node(self, node: str) -> str:
        mod_node = re.sub(self.pattern, "eval", node)
        if not node.endswith("_eval"):
            mod_node += "_eval"
        return mod_node

    def _sub_or_append_eval_to_input_values(self, inputs: Dict[str, str]) -> Dict[str, str]:
        mod_inputs: Dict[str, str] = {}
        for input, value in inputs.items():
            mvalue = re.sub(self.pattern, "eval", value)
            res: List[str] = []
            for s in mvalue.split(".")[:-1]:
                if not s.endswith("_eval"):
                    s += "_eval"
                res += s
            res += mvalue.split(".")[-1]
            mod_inputs[input] = ".".join(res)
        return mod_inputs

    def convert(self, node: str, inputs: Dict[str, Dict[str, str]]) -> Tuple[str, Dict[str, str]]:
        eval_node = self._sub_or_append_eval_to_node(node)
        eval_inputs = self._sub_or_append_eval_to_input_values(inputs)
        return eval_node, eval_inputs


class DAGExtender:
    nodes: Dict[str, Processor]
    edges: Dict[str, Dict[str, str]]

    _inputs2eval: Inputs2Eval = Inputs2Eval()

    def __init__(
        self,
        nodes: Dict[str, Processor],
        edges: DictConfig,
    ) -> None:
        self.nodes = nodes
        self.edges = edges

    def run(self) -> None:
        extended_nodes = self.nodes.copy()
        extended_edges = deepcopy(self.edges)

        for name, processor in self.nodes.items():
            if isinstance(processor, Estimator):
                input_names = processor.transformer_provider.inputs & processor.outputs
                eval_transformer = processor.transformer_provider
            else:
                input_names = self.edges[name]
                eval_transformer = processor  # what if DAG?
            eval_node, eval_inputs = self._inputs2eval.convert(input_names)
            extended_edges[eval_node] = eval_inputs
            extended_nodes[eval_node] = eval_transformer

        return extended_nodes, extended_edges
