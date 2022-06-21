import re
from dataclasses import dataclass
from functools import partial
from inspect import signature
from typing import Any, Dict, List, Pattern, Type, Union

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

    def convert(self, inputs: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        eval_inputs = inputs.copy()
        for node, inputs in eval_inputs.items():
            mod_node = self._sub_or_append_eval_to_node(node)
            mod_inputs = self._sub_or_append_eval_to_input_values(inputs)
            eval_inputs[mod_node] = mod_inputs
        return eval_inputs


class Runner:
    inputs: DictConfig
    pipeline: Dict[str, Processor]

    def __init__(
        self,
        inputs: DictConfig,
        pipeline: Dict[str, Processor],
        storage: Storage,
    ) -> None:
        self.inputs = inputs
        self.pipeline = pipeline
        self.storage = storage

    def run(self) -> None:
        expanded_pipeline = self.pipeline.copy()
        for name, processor in self.pipeline.items():
            proc_inputs = self.inputs[name]
            args = self.storage.load(proc_inputs)
            results = processor.process(**args)
            self.storage.save(results)

            if isinstance(processor, Estimator):
                partial_transformer = processor._transformer_provider.partial
                input_params = self._get_eval_params(partial_transformer, results)
                eval_transformer = partial_transformer(input_params)
            else:
                eval_transformer = processor
            expanded_pipeline.append(eval_transformer)

    def _get_eval_params(
        self, partial_transformer: partial[Transformer], results: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {k: results[v] for k, v in signature(partial_transformer).parameters}
