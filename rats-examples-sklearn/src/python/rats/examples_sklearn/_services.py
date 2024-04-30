from rats import apps

from ._lr_pipeline_container import LRPipelineContainer


class Services:
    TRAIN_PIPELINE = apps.autoid(LRPipelineContainer.training_pipeline)
    PREDICT_PIPELINE = apps.autoid(LRPipelineContainer.prediction_pipeline)
