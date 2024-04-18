from collections.abc import Callable, Iterator, Sequence
from functools import wraps
from inspect import signature
from typing import Any, Concatenate, Generic, ParamSpec, TypeVar, cast

from rats import apps
from rats.processors import ux

from ._pipeline_container import PipelineContainer

T_ServiceType = TypeVar("T_ServiceType")
P = ParamSpec("P")
T_Container = TypeVar("T_Container", bound=PipelineContainer)
TInputs = TypeVar("TInputs", bound=ux.Inputs, covariant=True)
TOutputs = TypeVar("TOutputs", bound=ux.Outputs, covariant=True)


# A class with a __new__ method is equivalent to a function, with the advantage that it can have a
# generic type arguments.
class _process_method_to_task_method(Generic[TInputs, TOutputs]):
    """Convert a process method to a method returning a task wrapping over the process method."""

    def __new__(
        cls,
        process_method: Callable[Concatenate[T_Container, P], ux.ProcessorOutput],
    ) -> Callable[[T_Container], ux.Pipeline[TInputs, TOutputs]]:
        class _Processor(ux.IProcess):
            process = process_method

        _Processor.__name__ = process_method.__name__

        def get_task(self: T_Container) -> ux.Pipeline[TInputs, TOutputs]:
            return ux.Task[TInputs, TOutputs](_Processor)

        get_task.__module__ = process_method.__module__
        get_task.__name__ = process_method.__name__
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
        process_method: Callable[Concatenate[T_Container, P], ux.ProcessorOutput],
    ) -> Callable[[T_Container], ux.Pipeline[TInputs, TOutputs]]:
        task_method = _process_method_to_task_method[TInputs, TOutputs](process_method)
        return apps.autoid_service(task_method)


def pipeline(
    pipeline_method: Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]],
) -> Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]]:
    """Decorator creating a pipeline service.

    The name of the pipeline will be name of the method.
    """
    name = pipeline_method.__name__

    @wraps(pipeline_method)
    def get_pipeline_and_rename(
        self: T_Container,
    ) -> ux.Pipeline[ux.TInputs, ux.TOutputs]:
        pipeline = pipeline_method(self)
        if pipeline.name != name:
            pipeline = pipeline.decorate(name)
        return pipeline

    return apps.autoid_service(get_pipeline_and_rename)


def dependencies(
    method: Callable[[T_Container, TOutputs, TInputs], Iterator[ux.DependencyOp[Any]]],
) -> Callable[[T_Container], Sequence[ux.DependencyOp[Any]]]:
    method_signature = signature(method)
    # get names of method parameters by position:
    method_parameter_names = list(method_signature.parameters)
    source_name = method_parameter_names[1]
    target_name = method_parameter_names[2]

    def get_dependencies(self: T_Container) -> Sequence[ux.DependencyOp[Any]]:
        source_id = apps.method_service_id(getattr(self, source_name))
        target_id = apps.method_service_id(getattr(self, target_name))
        source = self.get(source_id)
        target = self.get(target_id)
        return tuple(method(self, source, target))

    get_dependencies.__module__ = method.__module__
    get_dependencies.__name__ = method.__name__
    get_dependencies.__qualname__ = method.__qualname__

    return apps.autoid_service(get_dependencies)


def combine(
    method: Callable[Concatenate[T_Container, P], ux.Pipeline[ux.TInputs, ux.TOutputs]],
) -> Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]]:
    method_signature = signature(method)
    # get names of method parameters by position:
    method_parameter_names = list(method_signature.parameters)

    def get_pipeline(self: T_Container) -> ux.Pipeline[ux.TInputs, ux.TOutputs]:
        ids = [apps.method_service_id(getattr(self, name)) for name in method_parameter_names[1:]]
        services = [self.get(id) for id in ids]
        pipelines = [service for service in services if isinstance(service, ux.Pipeline)]
        dependencies = [service for service in services if isinstance(service, ux.DependencyOp)]
        pipeline = self.combine(
            pipelines=pipelines,
            dependencies=dependencies,
        )
        return cast(ux.Pipeline[ux.TInputs, ux.TOutputs], pipeline)

    get_pipeline.__module__ = method.__module__
    get_pipeline.__name__ = method.__name__
    get_pipeline.__qualname__ = method.__qualname__

    return apps.autoid_service(get_pipeline)
