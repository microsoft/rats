import base64
import logging
import os
import pickle
import shutil
import subprocess
import tempfile
import uuid
from typing import Dict, List, Tuple, Type, cast

from oneml.processors_script import run_processor_cmd, serialize_processor

from .dag import DAG, InputPortAddress, OutputPortAddress, SimpleNodeName
from .data_annotation import Data
from .processor import InputPortName, OutputPortName, Processor
from .processor_decorators import processor, processor_using_signature
from .return_annotation import Output
from .run_context import RunContext

logger = logging.getLogger(__name__)


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
        with open(self.path, "wb") as fle:
            pickle.dump(input, fle)
        logger.debug("wrote object to %s.", self.path)
        return dict()


@processor_using_signature
class ReadProcessor:
    def __init__(
        self, base_path: str, inputPortName: InputPortName, data_type: Type[Data]
    ) -> None:
        self.inputPortName = inputPortName
        self.path = os.path.join(base_path, inputPortName)
        self.data_type = data_type

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return dict()

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return {OutputPortName("output"): self.data_type}

    def _process(self, run_context: RunContext) -> Output(output=Data):
        with open(self.path, "rb") as fle:
            o = pickle.load(fle)
        logger.debug("read object from %s.", self.path)
        return dict(output=o)


@processor
class RunInSubProcess:
    def __init__(self, wrapped_processor: Processor):
        self.wrapped_processor = wrapped_processor
        self.dag, self.scratch_path, self.read_nodes, self.write_nodes = self._get_wrapping_dag(
            wrapped_processor
        )
        self.serialized_dag = serialize_processor(self.dag)

    def _get_wrapping_dag(
        self, wrapped_processor: Processor
    ) -> Tuple[DAG, str, List[ReadProcessor], List[WriteProcessor]]:
        scratch_path = os.path.join(
            tempfile.gettempdir(), base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("UTF-8")
        )

        nodes: Dict[SimpleNodeName, Processor] = dict()
        edges: Dict[InputPortAddress, OutputPortAddress] = dict()
        processor_node_name = SimpleNodeName("processor")
        nodes[processor_node_name] = wrapped_processor

        read_nodes: List[ReadProcessor] = []
        write_nodes: List[WriteProcessor] = []
        for inputPortName, inputPortDataType in wrapped_processor.get_input_schema().items():
            read_node_name = SimpleNodeName(f"read:{inputPortName}")
            read_node = ReadProcessor(scratch_path, inputPortName, inputPortDataType)
            nodes[read_node_name] = read_node
            read_nodes.append(read_node)
            edges[InputPortAddress(processor_node_name, inputPortName)] = OutputPortAddress(
                read_node_name, "output"
            )
        for outputPortName, outputPortDataType in wrapped_processor.get_output_schema().items():
            write_node_name = SimpleNodeName(f"write:{outputPortName}")
            write_node = WriteProcessor(scratch_path, outputPortName, outputPortDataType)
            nodes[write_node_name] = write_node
            write_nodes.append(write_node)
            edges[InputPortAddress(write_node_name, "input")] = OutputPortAddress(
                processor_node_name, outputPortName
            )
        dag = DAG(
            nodes=nodes,
            input_edges={},
            output_edges={},
            edges=edges,
        )
        return dag, scratch_path, read_nodes, write_nodes

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return self.wrapped_processor.get_input_schema()

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return self.wrapped_processor.get_output_schema()

    def _write_inputs(self, inputs: Dict[InputPortName, Data]) -> None:
        def write_for_node_to_read(node: ReadProcessor, value: Data) -> None:
            with open(node.path, "wb") as fle:
                pickle.dump(value, fle)
            logger.debug("wrote input to %s.", node.path)

        os.makedirs(self.scratch_path)
        for node in self.read_nodes:
            input_value = inputs[node.inputPortName]
            write_for_node_to_read(node, input_value)

    def _read_outputs(self) -> Dict[OutputPortName, Data]:
        def read_what_node_wrote(node: WriteProcessor) -> Data:
            with open(node.path, "rb") as fle:
                value = pickle.load(fle)
            logger.debug("read output from %s.", node.path)
            return value

        outputs = {node.outputPortName: read_what_node_wrote(node) for node in self.write_nodes}

        shutil.rmtree(self.scratch_path, ignore_errors=True)
        return outputs

    def _run_process(self, run_context: RunContext) -> None:
        cmd = [run_processor_cmd, run_context.identifier, self.serialized_dag]
        logger.debug("Forking to run command: %s", cmd)
        subprocess.run(cmd, check=True)
        logger.debug("Completed run command: %s", cmd)

    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        self._write_inputs(cast(Dict[InputPortName, Data], inputs))
        self._run_process(run_context)
        outputs = self._read_outputs()
        return outputs
