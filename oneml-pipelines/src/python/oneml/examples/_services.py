from typing import NamedTuple

from oneml.services import ContextId, ServiceId, scoped_context_ids, scoped_service_ids

from ._pipeline import HelloWorldPipeline


@scoped_service_ids
class OnemlExampleServices:
    EXAMPLE_PIPELINE = ServiceId[HelloWorldPipeline]("example-pipeline")


class ExampleCustomThing(NamedTuple):
    name: str


@scoped_context_ids
class OnemlExampleContexts:
    CUSTOM_THING = ContextId[ExampleCustomThing]("custom-thing")
