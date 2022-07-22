"""
    A TrainAndPredict is a pipeline that trains on train data and evaluates on train and holdout
    data.
    To that end, the TrainAndPredict has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"

"""
from typing import Set

from munch import Munch

from ..processors import DAG, Processor


def _build_train_and_predict_from_three_processors(
    fit: Processor, train_predict: Processor, holdout_predict: Processor
):
    def verify() -> None:
        fit_outputs: Set[str] = set(fit.get_output_schema().keys())
        train_predict_inputs: Set[str] = set(train_predict.get_input_schema().keys())
        holdout_predict_inputs: Set[str] = set(holdout_predict.get_input_schema().keys())
        assert fit_outputs.issubset(train_predict_inputs)
        assert fit_outputs.issubset(holdout_predict_inputs)

    verify()

    nodes = dict(fit=fit, train_predict=train_predict, holdout_predict=holdout_predict)
    input_edges = dict()
    edges = dict()
    output_edges = dict()
    for input_port in fit.get_input_schema().keys():
        input_edges[f"fit.{input_port}"] = f"train_{input_port}"
    for input_port in train_predict.get_input_schema().keys():
        if input_port not in fit.get_output_schema():
            input_edges[f"train_predict.{input_port}"] = f"train_{input_port}"
        else:
            edges[f"train_predict.{input_port}"] = f"fit.{input_port}"
    for input_port in holdout_predict.get_input_schema().keys():
        if input_port not in fit.get_output_schema():
            input_edges[f"holdout_predict.{input_port}"] = f"holdout_{input_port}"
        else:
            edges[f"holdout_predict.{input_port}"] = f"fit.{input_port}"
    for output_port in train_predict.get_output_schema():
        output_edges[f"train_{output_port}"] = f"train_predict.{output_port}"
    for output_port in holdout_predict.get_output_schema():
        output_edges[f"holdout_{output_port}"] = f"holdout_predict.{output_port}"
    return Munch(nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges)


class TrainAndPredictFromTwoProcessors(DAG):
    """A TrainAndPredict DAG where the predict stage is identical for train and holdout.

    A TrainAndPredict is a pipeline that trains on train data and evaluates on train and holdout
    data.
    To that end, the TrainAndPredict has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"

    This class provides a way to construct a standard TrainAndPredict, where the predict stage is
    identical for both train and holdout data.

    Args:
        fit: a Processor that fits that training data and outputs the fitted model or
            parameters.
        predict: a Processor that takes the output of fit plus data and produces predictions.

    The three nodes of the DAG will be
    * "fit" -> fit
    * "train_predict" -> predict
    * "holdout_predict" -> holdout

    The union of the input ports of fit and predict will become the TrainAndPredict's train input
    ports (a "train_" prefix will be added to their name).
    The input ports of predict will become the TrainAndPredict's holdout input ports (a "holdout_"
    prefix will be added to their name).

    The outputs of fit will be passed as inputs to both predict nodes.

    The outputs of each predict node will become train/holdout output ports of the TrainAndPredict
    (a "train_"/"holdout_" prefix will be added to their name).
    """

    def __init__(self, fit: Processor, predict: Processor):
        m = _build_train_and_predict_from_three_processors(fit, predict, predict)
        super().__init__(
            nodes=m.nodes, input_edges=m.input_edges, edges=m.edges, output_edges=m.output_edges
        )


class TrainAndPredictFromThreeProcessors(DAG):
    """A TrainAndPredict DAG supporting different predict stages for train and holdout.

    A TrainAndPredict is a pipeline that trains on train data and evaluates on train and holdout
    data.
    To that end, the TrainAndPredict has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"

    This class provides a way to construct a TrainAndPredict for non-standard cases, where we need
    a different predict stage for train and holdout data.  For example, if we need to exlude
    train-TCRs from holdout data.

    Args:
        fit: a Processor that fits that training data and outputs the fitted model or
            parameters.
        train_predict: a Processor that takes the output of fit plus train data and produces
            predictions.
        holdout_predict: a Processor that takes the output of fit plus holdout data and
            produces predictions.

    The three nodes of the DAG will be
    * "fit" -> fit
    * "train_predict" -> train_predict
    * "holdout_predict" -> train_holdout

    The union of the input ports of fit and train_predict will become the TrainAndPredict's train
    input ports (a "train_" prefix will be added to their name).
    The input ports of holdout_predict will become the TrainAndPredict's holdout input ports (a
    "holdout_" prefix will be added to their name).

    The outputs of fit will be passed as inputs to both predict nodes.

    The outputs of each predict node will become train/holdout output ports of the TrainAndPredict
    (a "train_"/"holdout_" prefix will be added to their name).
    """

    def __init__(self, fit: Processor, train_predict: Processor, holdout_predict: Processor):
        m = _build_train_and_predict_from_three_processors(fit, train_predict, holdout_predict)
        super().__init__(
            nodes=m.nodes, input_edges=m.input_edges, edges=m.edges, output_edges=m.output_edges
        )
