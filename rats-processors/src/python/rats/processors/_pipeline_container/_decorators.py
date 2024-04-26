from collections.abc import Callable
from functools import wraps
from typing import Concatenate, Generic, ParamSpec, TypeVar

from rats import apps
from rats.processors._legacy_subpackages import Task
from rats.processors._legacy_subpackages import typing as rpt

T_ServiceType = TypeVar("T_ServiceType")
P = ParamSpec("P")
T_Container = TypeVar("T_Container", bound=apps.Container)
TInputs = TypeVar("TInputs", bound=rpt.Inputs, covariant=True)
TOutputs = TypeVar("TOutputs", bound=rpt.Outputs, covariant=True)


# A class with a __new__ method is equivalent to a function, with the advantage that it can have a
# generic type arguments.
class _method_to_task_provider(Generic[TInputs, TOutputs]):
    """Convert a process method to a method returning a task wrapping over the process method."""

    def __new__(
        cls,
        method: Callable[Concatenate[T_Container, P], rpt.ProcessorOutput],
    ) -> Callable[[T_Container], rpt.Pipeline[TInputs, TOutputs]]:
        def get_task(container: T_Container) -> rpt.Pipeline[TInputs, TOutputs]:
            class _Processor:
                @wraps(method)
                def process(self, *args: P.args, **kwargs: P.kwargs) -> rpt.ProcessorOutput:
                    return method(container, *args, **kwargs)

            _Processor.__name__ = method.__name__

            return Task[TInputs, TOutputs](_Processor)

        get_task.__name__ = method.__name__
        get_task.__module__ = method.__module__
        get_task.__qualname__ = method.__qualname__
        get_task.__doc__ = method.__doc__

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
        method: Callable[Concatenate[T_Container, P], rpt.ProcessorOutput],
    ) -> Callable[[T_Container], rpt.Pipeline[TInputs, TOutputs]]:
        task_method = _method_to_task_provider[TInputs, TOutputs](method)
        return apps.autoid_service(task_method)


def pipeline(
    pipeline_method: Callable[[T_Container], rpt.Pipeline[rpt.TInputs, rpt.TOutputs]],
) -> Callable[[T_Container], rpt.Pipeline[rpt.TInputs, rpt.TOutputs]]:
    """Decorator creating a pipeline service.

    The name of the pipeline will be name of the method.
    """
    name = pipeline_method.__name__

    @wraps(pipeline_method)
    def get_pipeline_and_rename(
        container: T_Container,
    ) -> rpt.Pipeline[rpt.TInputs, rpt.TOutputs]:
        pipeline = pipeline_method(container)
        if pipeline.name != name:
            pipeline = pipeline.decorate(name)
        return pipeline

    return apps.autoid_service(get_pipeline_and_rename)
