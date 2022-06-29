from typing import Dict

import numpy as np
import numpy.typing as npt
from munch import munchify

from ..processors.data_annotation import Data
from ..processors.processor import InputPortName, OutputPortName
from ..processors.processor_decorators import processor, processor_using_signature
from ..processors.return_annotation import Output
from ..processors.run_context import RunContext


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
