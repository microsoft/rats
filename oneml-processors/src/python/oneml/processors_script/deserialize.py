import base64

import dill

from oneml.processors import Processor


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
