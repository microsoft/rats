"""General pipeline building functionality."""

from ._app_plugin import (
    RatsProcessorsPipelineOperationsPlugin,
    RatsProcessorsPipelineOperationsServices,
)
from ._build_manifest_processor import Manifest
from ._collection_to_dict import CollectionToDict, DictToCollection
from ._duplicate_pipeline import DuplicatePipeline, DuplicatePipelineConf
from ._expose_given_outputs import ExposeGivenOutputs

__all__ = [
    "Manifest",
    "CollectionToDict",
    "DictToCollection",
    "RatsProcessorsPipelineOperationsPlugin",
    "DuplicatePipeline",
    "DuplicatePipelineConf",
    "ExposeGivenOutputs",
    "RatsProcessorsPipelineOperationsServices",
]
