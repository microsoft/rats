# flake8: noqa
from typing import cast

import numpy as np
import numpy.typing as npt
import pytest
from munch import Munch

from oneml.processors.processor import Processor
from oneml.processors.processor_using_signature_decorator import processor_using_signature
from oneml.processors.return_annotation import Output
from oneml.processors.run_context import RunContext


class _TestRunContext(RunContext):
    def __init__(self):
        super().__init__(None)
        self.inputs = {}

    def log_inputs(self, **kwargs):
        self.inputs.update(kwargs)


def test_processing_func_taking_run_context():
    @processor_using_signature
    class P:
        def _process(
            self, run_context: RunContext, input1: int, input2: str
        ) -> Output(output1=float, output2=str, output3=npt.ArrayLike):
            test_run_context = cast(_TestRunContext, run_context)
            test_run_context.log_inputs(input1=input1, input2=input2)
            return Munch(
                output1=10.0,
                output2="sss",
                output3=np.arange(10),
            )

    assert issubclass(P, Processor)
    p = P()
    input_schema = p.get_input_schema()
    assert len(input_schema) == 2
    assert input_schema["input1"] == int
    assert input_schema["input2"] == str
    output_schema = p.get_output_schema()
    assert len(output_schema) == 3
    assert output_schema["output1"] == float
    assert output_schema["output2"] == str
    assert output_schema["output3"] == npt.ArrayLike

    trc = _TestRunContext()
    outputs = p.process(trc, input1=100, input2="inp")
    assert len(trc.inputs) == 2
    assert trc.inputs["input1"] == 100
    assert trc.inputs["input2"] == "inp"
    assert len(outputs) == 3
    assert outputs["output1"] == 10.0
    assert outputs["output2"] == "sss"
    assert (outputs["output3"] == np.arange(10)).all()


def test_processing_func_not_taking_run_context():
    inputs = {}

    @processor_using_signature
    class P:
        def _process(
            self, input1: int, input2: str
        ) -> Output(output1=float, output2=str, output3=int):
            inputs.update(dict(input1=input1, input2=input2))
            return Munch(output1=10.0, output2="sss", output3=20)

    assert issubclass(P, Processor)
    p = P()
    input_schema = p.get_input_schema()
    assert len(input_schema) == 2
    assert input_schema["input1"] == int
    assert input_schema["input2"] == str
    output_schema = p.get_output_schema()
    assert len(output_schema) == 3
    assert output_schema["output1"] == float
    assert output_schema["output2"] == str
    assert output_schema["output3"] == int

    trc = _TestRunContext()
    outputs = p.process(trc, input1=100, input2="inp")
    assert len(inputs) == 2
    assert inputs["input1"] == 100
    assert inputs["input2"] == "inp"
    assert len(outputs) == 3
    assert outputs["output1"] == 10.0
    assert outputs["output2"] == "sss"
    assert outputs["output3"] == 20


def test_processing_func_not_taking_inputs():
    @processor_using_signature
    class P:
        def _process(self) -> Output(output1=float, output2=str, output3=int):
            return Munch(output1=10.0, output2="sss", output3=20)

    assert issubclass(P, Processor)
    p = P()
    input_schema = p.get_input_schema()
    assert len(input_schema) == 0
    output_schema = p.get_output_schema()
    assert len(output_schema) == 3
    assert output_schema["output1"] == float
    assert output_schema["output2"] == str
    assert output_schema["output3"] == int

    trc = _TestRunContext()
    outputs = p.process(trc)
    assert len(outputs) == 3
    assert outputs["output1"] == 10.0
    assert outputs["output2"] == "sss"
    assert outputs["output3"] == 20


def test_processing_func_taking_only_run_context():
    @processor_using_signature
    class P:
        def _process(self, run_context: RunContext) -> Output():
            return Munch()

    assert issubclass(P, Processor)
    p = P()
    input_schema = p.get_input_schema()
    assert len(input_schema) == 0
    output_schema = p.get_output_schema()
    assert len(output_schema) == 0

    trc = _TestRunContext()
    outputs = p.process(trc)
    assert len(outputs) == 0


def test_invalid_processing_func():
    with pytest.raises(TypeError):

        @processor_using_signature
        class P:
            pass

    with pytest.raises(TypeError):

        @processor_using_signature
        class P:
            def _process(this, input1: int) -> Output():
                pass

    with pytest.raises(TypeError):

        @processor_using_signature
        class P:
            def _process(self, input1: int, run_context: RunContext) -> Output():
                pass

    with pytest.raises(TypeError):

        @processor_using_signature
        class P:
            def _process(self, input1: int, run_context: float) -> Output():
                pass

    with pytest.raises(TypeError):

        @processor_using_signature
        class P:
            def _process(self, input1: int, a: RunContext) -> Output():
                pass

    with pytest.raises(TypeError):

        @processor_using_signature
        class P:
            def _process(self, run_context: float, input1: int) -> Output():
                pass

    with pytest.raises(TypeError):

        @processor_using_signature
        class P:
            def _process(self, a: RunContext, input1: int) -> Output():
                pass
