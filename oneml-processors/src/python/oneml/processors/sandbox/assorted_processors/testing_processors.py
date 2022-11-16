# type: ignore
# flake8: noqa
from typing import Dict

import numpy as np
import numpy.typing as npt
from munch import munchify

from ..processors import (
    Data,
    InputPortName,
    Output,
    OutputPortName,
    RunContext,
    processor,
    processor_using_signature,
)


@processor_using_signature
class ArrayDotProduct:
    def _process(self, left: npt.ArrayLike, right: npt.ArrayLike) -> Output(output=npt.ArrayLike):
        return munchify(dict(output=np.dot(left, right)))


@processor
class ArrayConcatenator:
    def __init__(self, num_inputs: int):
        self.num_inputs = num_inputs

    def get_input_schema(self) -> Dict[InputPortName, Data]:
        return {InputPortName(f"input{i}"): npt.ArrayLike for i in range(self.num_inputs)}

    def get_output_schema(self) -> Dict[OutputPortName, Data]:
        return {OutputPortName("output"): npt.ArrayLike}

    def process(
        self, run_context: RunContext, **inputs: npt.ArrayLike
    ) -> Output(output=npt.ArrayLike):
        return munchify(
            dict(
                output=np.concatenate(
                    [inputs[f"input{i}"].reshape(-1) for i in range(self.num_inputs)]
                )
            )
        )