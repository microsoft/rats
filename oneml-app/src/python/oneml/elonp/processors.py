import inspect
import logging
from typing import Any, Dict, Protocol, Type, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Processor(Protocol):
    def get_input_schema(self) -> Dict[str, Type]:
        ...

    def get_output_schema(self) -> Dict[str, Type]:
        ...

    def process(self, **kwds: Any) -> Dict[str, Any]:
        ...


@runtime_checkable
class ProcessingFunc(Protocol):
    def process(self, **kwds: Any) -> Dict:
        ...


def processor_from_func(processing_func_class: Type[ProcessingFunc]) -> Type[Processor]:
    signature = inspect.signature(processing_func_class.process)
    
    def get_input_schema(self) -> Dict[str, Type]:    
        parameters = list(signature.parameters.items())[1:]
        return {
            param_name: parameter.annotation
            for (param_name, parameter) in parameters
        }

    def get_output_schema(self) -> Dict[str, Type]:
        return signature.return_annotation.__annotations__

    processing_func_class.get_input_schema = get_input_schema
    processing_func_class.get_output_schema = get_output_schema
    
    return processing_func_class
