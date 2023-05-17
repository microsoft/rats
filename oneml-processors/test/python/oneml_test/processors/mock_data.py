import logging
from dataclasses import dataclass

from oneml.pipelines.data._serialization import ISerializeData
from oneml.pipelines.session import DataTypeId

logger = logging.getLogger(__name__)


@dataclass
class Array:
    v: str

    def __repr__(self) -> str:
        return self.v


@dataclass
class Model:
    x: Array
    y: Array

    def __repr__(self) -> str:
        return f"Model({self.x} ; {self.y})"


class DataTypeIds:
    ARRAY = DataTypeId[Array]("array")
    MODEL = DataTypeId[Model]("model")


class ModelSerializer(ISerializeData[Model]):
    def serialize(self, data: Model) -> str:
        return f"{data.x.v},{data.y.v}"

    def deserialize(self, data: str) -> Model:
        # TODO: how do we return something other than dicts?
        #       maybe we need to pass in the type?
        logger.debug(f"deserializing data: {data}")
        x, y = tuple(Array(s) for s in data.split(","))
        return Model(x=x, y=y)
