"""General pipeline building functionality."""

from ._app_plugin import (
    OnemlProcessorsPipelineOperationsPlugin,
    OnemlProcessorsPipelineOperationsServices,
)
from ._build_manifest_processor import Manifest
from ._collection_to_dict import CollectionToDict, DictToCollection
from ._duplicate_pipeline import DuplicatePipeline, DuplicatePipelineConf
from ._expose_given_outputs import ExposeGivenOutputs
from ._pipeline_provider import ExecutablePipeline, IProvidePipeline, ITransformPipeline

__all__ = [
    "Manifest",
    "CollectionToDict",
    "DictToCollection",
    "OnemlProcessorsPipelineOperationsPlugin",
    "DuplicatePipeline",
    "DuplicatePipelineConf",
    "ExposeGivenOutputs",
    "ExecutablePipeline",
    "IProvidePipeline",
    "ITransformPipeline",
    "OnemlProcessorsPipelineOperationsServices",
]
