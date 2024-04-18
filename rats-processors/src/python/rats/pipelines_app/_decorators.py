from collections.abc import Callable
from functools import wraps
from typing import Concatenate, Generic, ParamSpec, TypeVar

from rats import apps
from rats.processors import ux

T_ServiceType = TypeVar("T_ServiceType")
P = ParamSpec("P")
T_Container = TypeVar("T_Container", bound=apps.Container)
TInputs = TypeVar("TInputs", bound=ux.Inputs, covariant=True)
TOutputs = TypeVar("TOutputs", bound=ux.Outputs, covariant=True)


# A class with a __new__ method is equivalent to a function, with the advantage that it can have a
# generic type arguments.
class _process_method_to_task_method(Generic[TInputs, TOutputs]):
    """Convert a process method to a method returning a task wrapping over the process method."""

    def __new__(
        cls,
        process_method: Callable[Concatenate[T_Container, P], ux.T_Processor_Output],
    ) -> Callable[[T_Container], ux.Pipeline[TInputs, TOutputs]]:
        class _Processor(ux.IProcess):
            process = process_method

        _Processor.__name__ = process_method.__name__

        def get_task(self: T_Container) -> ux.Pipeline[TInputs, TOutputs]:
            return ux.Task[TInputs, TOutputs](_Processor)

        get_task.__name__ = process_method.__name__
        get_task.__module__ = process_method.__module__
        get_task.__qualname__ = process_method.__qualname__
        get_task.__doc__ = process_method.__doc__

        return get_task


# A class with a __new__ method is equivalent to a function, with the advantage that it can have a
# generic type arguments.  Using this mechanism here means we can decorate a processor method with
# @task[MyInputs, MyOutputs] and get the correct pipeline output type.
class task(Generic[TInputs, TOutputs]):
    """Decorator creating a pipeline service from a process method.

    The pipeline will be a task wrapping over the method.

    The name of the pipeline will be name of the method.
    """

    def __new__(
        cls,
        process_method: Callable[Concatenate[T_Container, P], ux.T_Processor_Output],
    ) -> Callable[[T_Container], ux.Pipeline[TInputs, TOutputs]]:
        task_method = _process_method_to_task_method[TInputs, TOutputs](process_method)
        return apps.autoid_service(task_method)


def pipeline(
    get_pipeline_method: Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]],
) -> Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]]:
    """Decorator creating a pipeline service.

    The name of the pipeline will be name of the method.
    """
    name = get_pipeline_method.__name__

    @wraps(get_pipeline_method)
    def get_pipeline_and_rename(
        self: T_Container,
    ) -> ux.Pipeline[ux.TInputs, ux.TOutputs]:
        pipeline = get_pipeline_method(self)
        if pipeline.name != name:
            pipeline = pipeline.decorate(name)
        return pipeline

    return apps.autoid_service(get_pipeline_and_rename)
