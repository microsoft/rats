from .parts import Step, Result, Out
from typing import List, Any, Dict
import numpy as np


def assign_inputs(target: Step, *sources: List[Step]) -> Step:
    for k, s in target._schema:
        if s.is_input:
            for src in sources:
                if k in src._schema:
                    target = target._assign(**{k: src[k]})
                    break
    return target


def set_outputs(result: Result, *steps: List[Step]) -> None:
    # similar but assigns outputs (reverse order?)
    pass


def cartesian_product(vals: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    pass


def merge_schemas(inputs: List[Step] = [], outputs: List[Step] = [], both: List[Step] = []):
    pass


class Splitter(Step):

    # seems like the easiest way to export train & val splits is as Steps
    # so they can have multiple output attributes
    # but that also seems counter-intuitive, these "Steps" don't do anything

    train: Out[Step]

    val: Out[Step]


class HyperGridSearch(Step):

    parameters: Dict[str, List[Any]]  # hyperparameter values to search through

    splitter: Splitter

    modeler: Step  # pipeline to be trained

    metric: Step  # step that takes modeler output and produces a single scalar "metric" output

    @property
    def _schema(self):
        """schema is dynamic based on sub-steps"""
        # return merge_schemas(inputs=[self.modeler, self.metric], outputs=[self.modeler])
        return self.modeler._schema

    def _run(self, result: Result) -> None:
        # for now use just single train, val split for simplicity; real impl would be k-fold
        train, val = self._runner.schedule(assign_inputs(self.splitter, self))[['train', 'val']]
        # schedule asynchronous pipeline for each 
        metrics = []
        parametrizations = cartesian_product(self.parameters)
        for p in parametrizations:
            # train modeler on train split
            est_i = self._runner.schedule(assign_inputs(self.modeler._assign(**p), train, self))
            # predict results on validation split
            fitted_i = self._runner.schedule(assign_inputs(est_i.fitted, val, self))
            # calculate metrics
            metrics_i = self._runner.schedule(assign_inputs(self.metrics, fitted_i, val, self))
            # append delayed result to list
            metrics.append(metrics_i.metric)
        # wait for everything to finish, turn from List[Future[float]] to List[float]
        metrics = self._runner.wait(*metrics)
        best_i = np.argmax(metrics)
        # train modeler with best parameter settings
        best = self._runner.schedule(assign_inputs(self.modeler._assign(**parametrizations[best_i]), self))
        # export all outputs from best, including fitted model
        set_outputs(result, best)
        # report resulting artifacts
        result.parametrizations = parametrizations
        result.metrics = metrics
