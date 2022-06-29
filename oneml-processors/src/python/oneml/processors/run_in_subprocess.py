import base64
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from typing import Dict, Type, cast

from oneml.processors_script import run_processor_cmd

from .data_annotation import Data
from .processor import InputPortName, OutputPortName, Processor
from .processor_decorators import processor
from .run_context import RunContext
from .serialization import load_data, save_data, serialize_processor

logger = logging.getLogger(__name__)


@processor
class RunInSubProcess:
    def __init__(self, wrapped_processor: Processor):
        self.wrapped_processor = wrapped_processor
        self.serialized_processor = serialize_processor(wrapped_processor)
        self.scratch_path = os.path.join(
            tempfile.gettempdir(), base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("UTF-8")
        )
        self.input_path = os.path.join(self.scratch_path, "inputs")
        self.output_path = os.path.join(self.scratch_path, "outputs")

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return self.wrapped_processor.get_input_schema()

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return self.wrapped_processor.get_output_schema()

    def _write_inputs(self, inputs: Dict[InputPortName, Data]) -> None:
        def write_for_port(port_name: InputPortName, value: Data) -> None:
            path = os.path.join(self.input_path, port_name)
            save_data(path, value)

        os.makedirs(self.scratch_path)
        for input_port_name in self.get_input_schema().keys():
            input_value = inputs[input_port_name]
            write_for_port(input_port_name, input_value)

    def _read_outputs(self) -> Dict[OutputPortName, Data]:
        def read_for_port(port_name: OutputPortName) -> Data:
            path = os.path.join(self.output_path, port_name)
            return load_data(path)

        outputs = {
            output_port_name: read_for_port(output_port_name)
            for output_port_name in self.get_output_schema().keys()
        }

        shutil.rmtree(self.scratch_path, ignore_errors=True)
        return outputs

    def _run_process(self, run_context: RunContext) -> None:
        cmd = [
            run_processor_cmd,
            run_context.identifier,
            self.serialized_processor,
            self.input_path,
            self.output_path,
        ]
        logger.debug("Forking to run command: %s", cmd)
        subprocess.run(cmd, check=True)
        logger.debug("Completed run command: %s", cmd)

    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        self._write_inputs(cast(Dict[InputPortName, Data], inputs))
        self._run_process(run_context)
        outputs = self._read_outputs()
        return outputs
