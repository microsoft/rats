# flake8: noqa
# type: ignore
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Union

from oneml.pipelines import IExecutable, IManageStorageItems, StorageItem, StorageItemKey
from oneml.processors import (
    InputPortName,
    NodeName,
    OutputPortAddress,
    OutputPortName,
    Processor,
    RunContext,
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutableWrappingProcessingNode(IExecutable):
    run_context: RunContext
    storage: IManageStorageItems
    input_mappings: Dict[InputPortName, Union[InputPortName, OutputPortAddress]]
    node_key: NodeName
    node: Processor

    def _load(self, key: str) -> Any:
        value: Any = self.storage.get_storage_item(StorageItemKey(key))
        logger.debug("Loaded input <%s.%s>.", self.node_key, key)
        return value

    def _save(self, key: str, value: Any) -> Any:
        self.storage.publish_storage_item(StorageItem(StorageItemKey(key), value))
        logger.debug("Saved output <%s.%s>.", self.node_key, key)

    def execute(self) -> None:
        logger.info("Executing <%s>.", self.node_key)
        inputs = {
            key: self._load(self.input_mappings[key])
            for key in self.node.get_input_schema().keys()
        }
        logger.debug("Executing <%s>.  Loaded inputs.", self.node_key)
        outputs: Dict[OutputPortName, Any] = self.node.process(self.run_context, **inputs)
        logger.debug("Executing <%s>.  Calculated outputs <%s>.", self.node_key, outputs.keys())
        for port_name, value in outputs.items():
            self._save(OutputPortAddress(self.node_key, port_name), value)
        logger.info("Executing <%s>.  Done.", self.node_key)
