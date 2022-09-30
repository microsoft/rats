# type: ignore
# flake8: noqa
import inspect
import logging
import sys
from abc import abstractmethod
from functools import wraps
from types import FunctionType
from typing import Dict, Optional, Type, TypeVar, Union, cast

from .data_annotation import Data
from .node import InputPortName, OutputPortName
from .processor import Processor
from .run_context import RunContext

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ProcessorUsingSignature(Processor):
    input_schema: Dict[InputPortName, Type[Data]]
    output_schema: Dict[OutputPortName, Type[Data]]

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return self.__class__.input_schema

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return self.__class__.output_schema

    @abstractmethod
    def _process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        ...

    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        return self._process(run_context, **inputs)


def processor_using_signature(cls: type) -> Type[Processor]:
    """Add all that is needed to convert a class into a Processor.

    Assumes:
        The class has a type-annotated `process` method.  The following applies to the `process` method:
            All parameters must be named.
            If there exists a `run_context: RunContext` parameter, it has to be the first parameter after `self`.
            The types of all parameters, except for `run_context`, derive from `Data`.
    """
    if Processor in cls.__mro__:
        raise TypeError(
            f"Do not list <Processor> as a base class when decorating a class using the "
            f"<processor_using_signature> decorator.  The decorator will do it for you."
        )

    def process_annotation(annotation: Union[str, type]) -> type:
        if type(annotation) == str:
            module_name = cls.__module__
            module = sys.modules[module_name]
            module_dict = module.__dict__
            return eval(annotation, module_dict)
        else:
            return cast(type, annotation)

    def is_run_context_param(parameter: inspect.Parameter) -> bool:
        parameter_type = process_annotation(parameter.annotation)
        suspected = parameter.name == "run_context" or parameter_type == RunContext
        if suspected:
            if parameter.name != "run_context":
                raise TypeError(
                    f"<{cls}._process> has a <RunContext> parameter called <{parameter.name}>. "
                    f"The <processor_using_signature> decorator expects a <RunContext> parameter, "
                    f"if it exists to be called <run_context>."
                )
            if parameter_type != RunContext:
                raise TypeError(
                    f"<{cls}._process> has a parameter called <run_context> of type "
                    f"<{parameter_type}>. The <processor_using_signature> decorator expects a "
                    f"<run_context> parameter, if it exists to be of type <RunContext>."
                )
        return suspected

    _process_method: Optional[FunctionType] = getattr(cls, "_process", None)
    if _process_method is None:
        raise TypeError(f"<{cls}> should have a type annotated _process method.")

    signature = inspect.signature(_process_method)

    parameters = list(signature.parameters.values())
    if parameters[0].name != "self":
        raise TypeError(f"First parameter of {cls}._process is expected to be <self>.")
    else:
        parameters = parameters[1:]
    if len(parameters) == 0:
        takes_run_context = False
    elif is_run_context_param(parameters[0]):
        takes_run_context = True
        parameters = parameters[1:]
    else:
        takes_run_context = False
    if any(map(is_run_context_param, parameters)):
        raise TypeError(
            f"<{cls}._process> has a <run_context> parameter that is not the right after <self>."
            f"The <processor_using_signature> decorator expects a <run_context> parameter, if it "
            f"exists, to be the first after <self>."
        )

    input_schema = {
        parameter.name: process_annotation(parameter.annotation) for parameter in parameters
    }
    output_schema = process_annotation(signature.return_annotation).__annotations__

    if not takes_run_context:

        def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
            outputs = {
                OutputPortName(port_name): value
                for port_name, value in self._process(**inputs).items()
            }
            return outputs

        new_param_sig = list(inspect.signature(process).parameters.values())[1]
        new_params = list(signature.parameters.values())
        new_params.insert(1, new_param_sig)
        new_sig = signature.replace(parameters=new_params)

        process = wraps(_process_method)(process)
        process.__signature__ = new_sig
        process.__name__ = "process"
    else:

        @wraps(_process_method)
        def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
            outputs = {
                OutputPortName(port_name): value
                for port_name, value in self._process(run_context, **inputs).items()
            }
            return outputs

        process.__name__ = "process"

    clsname = cls.__name__
    bases = (cls, ProcessorUsingSignature)
    attribs = dict(process=process, input_schema=input_schema, output_schema=output_schema)
    return type(clsname, bases, attribs)
