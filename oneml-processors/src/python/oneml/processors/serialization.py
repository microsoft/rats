import base64
import logging
import os
import pickle

import dill

from .data_annotation import Data
from .processor import Processor

logger = logging.getLogger(__name__)


def deserialize_processor(serialized_processor: str) -> Processor:
    base64_bytes = serialized_processor.encode("UTF-8")
    pickle_bytes = base64.b64decode(base64_bytes)
    processor = dill.loads(pickle_bytes)
    if not isinstance(processor, Processor):
        raise ValueError(
            f"Failed to deserialize argument into a Processor. "
            f"Got an object of type is <{type(processor)}>."
        )
    return processor


def serialize_processor(processor: Processor) -> str:
    pickle_bytes = dill.dumps(processor, recurse=True)
    base64_bytes = base64.b64encode(pickle_bytes)
    str = base64_bytes.decode("UTF-8")
    return str


def load_processor(path: str) -> Processor:
    with open(path, "r") as fle:
        s = fle.read()
    processor = deserialize_processor(s)
    logger.debug("read processor from %s.", path)
    return processor


def save_processor(path: str, processor: Processor) -> None:
    s = serialize_processor(processor)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fle:
        fle.write(s)
    logger.debug("wrote processor to %s.", path)


def load_data(path: str) -> Data:
    with open(path, "rb") as fle:
        o = pickle.load(fle)
    logger.debug("read object from %s.", path)
    return o


def save_data(path: str, data: Data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fle:
        pickle.dump(data, fle)
    logger.debug("wrote object to %s.", path)
