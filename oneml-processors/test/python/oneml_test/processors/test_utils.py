from oneml.processors._example_slr import ModelEval, ModelTrain, StandardizeEval, StandardizeTrain
from oneml.processors._frozendict import FrozenDict
from oneml.processors._utils import ProcessorCommonInputsOutputs


def test_frozendict() -> None:
    d1 = dict(boo="foo")
    fd: FrozenDict[str, str] = FrozenDict(d1)
    d2 = dict(fd)
    assert d1 == d2


def test_common_inputs_outputs() -> None:
    ProcessorCommonInputsOutputs.intersect_signatures(
        StandardizeTrain, StandardizeEval
    )
    ProcessorCommonInputsOutputs.intersect_signatures(ModelTrain, ModelEval)
