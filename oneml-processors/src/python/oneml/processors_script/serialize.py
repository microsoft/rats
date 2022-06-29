import base64

import dill

from oneml.processors import Processor


def serialize_processor(processor: Processor) -> str:
    pickle_bytes = dill.dumps(processor)
    base64_bytes = base64.b64encode(pickle_bytes)
    str = base64_bytes.decode("UTF-8")
    return str
