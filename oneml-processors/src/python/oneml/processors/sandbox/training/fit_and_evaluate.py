# type: ignore
# flake8: noqa
"""
    A FitAndEvaluate is a dag that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"

"""
from typing import Set

from munch import Munch

from ..processors import DAG, Processor


def _build_fit_and_evaluate_from_three_processors(
    fit: Processor, train_evaluate: Processor, holdout_evaluate: Processor
):
    def verify() -> None:
        fit_outputs: Set[str] = set(fit.get_output_schema().keys())
        train_evaluate_inputs: Set[str] = set(train_evaluate.get_input_schema().keys())
        holdout_evaluate_inputs: Set[str] = set(holdout_evaluate.get_input_schema().keys())
        assert fit_outputs.issubset(train_evaluate_inputs)
        assert fit_outputs.issubset(holdout_evaluate_inputs)

    verify()

    nodes = dict(fit=fit, train_evaluate=train_evaluate, holdout_evaluate=holdout_evaluate)
    input_edges = dict()
    edges = dict()
    output_edges = dict()
    for input_port in fit.get_input_schema().keys():
        input_edges[f"fit.{input_port}"] = f"train_{input_port}"
    for input_port in train_evaluate.get_input_schema().keys():
        if input_port not in fit.get_output_schema():
            input_edges[f"train_evaluate.{input_port}"] = f"train_{input_port}"
        else:
            edges[f"train_evaluate.{input_port}"] = f"fit.{input_port}"
    for input_port in holdout_evaluate.get_input_schema().keys():
        if input_port not in fit.get_output_schema():
            input_edges[f"holdout_evaluate.{input_port}"] = f"holdout_{input_port}"
        else:
            edges[f"holdout_evaluate.{input_port}"] = f"fit.{input_port}"
    for output_port in train_evaluate.get_output_schema():
        output_edges[f"train_{output_port}"] = f"train_evaluate.{output_port}"
    for output_port in holdout_evaluate.get_output_schema():
        output_edges[f"holdout_{output_port}"] = f"holdout_evaluate.{output_port}"
    return Munch(nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges)


class FitAndEvaluateFromTwoProcessors(DAG):
    """A FitAndEvaluate DAG where the evaluate stage is identical for train and holdout.

    A FitAndEvaluate is a dag that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"

    This class provides a way to construct a standard FitAndEvaluate, where the evaluate stage is
    identical for both train and holdout data.

    Args:
        fit: a Processor that fits that training data and outputs the fitted model or
            parameters.
        evaluate: a Processor that takes the output of fit plus data.

    The three nodes of the DAG will be
    * "fit" -> fit
    * "train_evaluate" -> evaluate
    * "holdout_evaluate" -> evaluate

    The union of the input ports of fit and evaluate will become the FitAndEvaluate's train input
    ports (a "train_" prefix will be added to their name).
    The input ports of evaluate will become the FitAndEvaluate's holdout input ports (a "holdout_"
    prefix will be added to their name).

    The outputs of fit will be passed as inputs to both evaluate nodes.

    The outputs of each evaluate node will become train/holdout output ports of the FitAndEvaluate
    (a "train_"/"holdout_" prefix will be added to their name).
    """

    def __init__(self, fit: Processor, evaluate: Processor):
        m = _build_fit_and_evaluate_from_three_processors(fit, evaluate, evaluate)
        super().__init__(
            nodes=m.nodes, input_edges=m.input_edges, edges=m.edges, output_edges=m.output_edges
        )


class FitAndEvaluateFromThreeProcessors(DAG):
    """A FitAndEvaluate DAG supporting different evaluate stages for train and holdout.

    A FitAndEvaluate is a dag that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"

    This class provides a way to construct a FitAndEvaluate for non-standard cases, where we need
    a different evaluate stage for train and holdout data.  For example, if we need to exlude
    train-TCRs from holdout data.

    Args:
        fit: a Processor that fits that training data and outputs the fitted model or
            parameters.
        train_evaluate: a Processor that takes the output of fit plus train data.
        holdout_evaluate: a Processor that takes the output of fit plus holdout data.

    The three nodes of the DAG will be
    * "fit" -> fit
    * "train_evaluate" -> train_evaluate
    * "holdout_evaluate" -> holdout_evaluate

    The union of the input ports of fit and train_evaluate will become the FitAndEvaluate's train
    input ports (a "train_" prefix will be added to their name).
    The input ports of holdout_evaluate will become the FitAndEvaluate's holdout input ports (a
    "holdout_" prefix will be added to their name).

    The outputs of fit will be passed as inputs to both evaluate nodes.

    The outputs of each evaluate node will become train/holdout output ports of the FitAndEvaluate
    (a "train_"/"holdout_" prefix will be added to their name).
    """

    def __init__(self, fit: Processor, train_evaluate: Processor, holdout_evaluate: Processor):
        m = _build_fit_and_evaluate_from_three_processors(fit, train_evaluate, holdout_evaluate)
        super().__init__(
            nodes=m.nodes, input_edges=m.input_edges, edges=m.edges, output_edges=m.output_edges
        )
