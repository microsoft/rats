import os
from typing import Dict, Type

from oneml.processors import (
    Data,
    InputPortName,
    Output,
    OutputPortName,
    RunContext,
    load_data,
    processor_using_signature,
    save_data,
)


@processor_using_signature
class ReadProcessor:
    def __init__(
        self, base_path: str, input_port_name: InputPortName, data_type: Type[Data]
    ) -> None:
        self.input_port_name = input_port_name
        self.path = os.path.join(base_path, input_port_name)
        self.data_type = data_type

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return dict()

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return {OutputPortName("output"): self.data_type}

    def _process(self, run_context: RunContext) -> Output(output=Data):
        o = load_data(self.path)
        return dict(output=o)


@processor_using_signature
class WriteProcessor:
    def __init__(
        self, base_path: str, outputPortName: OutputPortName, data_type: Type[Data]
    ) -> None:
        self.outputPortName = outputPortName
        self.path = os.path.join(base_path, outputPortName)
        self.data_type = data_type

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return {InputPortName("input"): self.data_type}

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return dict()

    def _process(self, run_context: RunContext, input: Data) -> Output():
        save_data(self.path, input)
        return dict()
