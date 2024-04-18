from rats import apps

from ._pipeline1 import ExamplePipelineContainer1
from ._pipeline2 import ExamplePipelineContainer2


class ExamplePipelineServices:
    P1 = apps.method_service_id(ExamplePipelineContainer1.p1)
    P2 = apps.method_service_id(ExamplePipelineContainer2.p2)
    LOAD_DATA = apps.method_service_id(ExamplePipelineContainer2.load_data)
    TRAIN_MODEL = apps.method_service_id(ExamplePipelineContainer2.train_model)
