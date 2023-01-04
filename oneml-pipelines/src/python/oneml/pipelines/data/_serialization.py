import json
import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Protocol, TypeVar

logger = logging.getLogger(__name__)

DataType = TypeVar("DataType")


@dataclass(frozen=True)
class DataTypeId(Generic[DataType]):
    key: str


DictDataType = DataTypeId[Dict[Any, Any]]("simple-dict")
DefaultDataType = DataTypeId[Dict[Any, Any]]("__default__")

"""
- how do we define mappings when we want to write data using spark but read it using pandas?
- should the mapping really be between types and data clients instead of serialization clients?
- serialization mapping could be a private detail of the blob client
"""


class ISerializeData(Protocol[DataType]):
    """
    A protocol for serializing a single data type.
    """

    # TODO: str is probably not the right return type
    @abstractmethod
    def serialize(self, data: DataType) -> str:
        pass

    @abstractmethod
    def deserialize(self, data: str) -> DataType:
        pass


class JsonSerializer(ISerializeData[DataType]):
    """
    Serializer for a single data type.
    """

    def serialize(self, data: DataType) -> str:
        # TODO: support dataclasses
        return json.dumps(data, indent=2)

    def deserialize(self, data: str) -> DataType:
        # TODO: how do we return something other than dicts?
        #       maybe we need to pass in the type?
        return json.loads(data)


class DemoSerializer(ISerializeData[DataType]):
    """
    Serializer for a single data type.
    """

    def serialize(self, data: DataType) -> str:
        logger.warning("demo serializer being used")
        return json.dumps(data, indent=2)

    def deserialize(self, data: str) -> DataType:
        logger.warning("demo serializer being used")
        return json.loads(data)


class ISerializeDataTypes(Protocol):
    """
    A client that can serialize and deserialize data types.

    Given a data type id, and its data, it can serialize it to a string.
    Given a data type id, and a string, it can deserialize it to its data.
    """

    @abstractmethod
    def serialize(self, data_id: DataTypeId[DataType], data: DataType) -> str:
        pass

    @abstractmethod
    def deserialize(self, data_id: DataTypeId[DataType], data: str) -> DataType:
        pass


class IRegisterSerializers(Protocol):
    @abstractmethod
    def register(
        self,
        data_id: DataTypeId[DataType],
        serializer: ISerializeData[DataType],
    ) -> None:
        pass


class SerializationClient(IRegisterSerializers, ISerializeDataTypes):

    _serializers: Dict[DataTypeId[Any], ISerializeData[Any]]

    def __init__(self) -> None:
        self._serializers = {}
        self._default_serializer = JsonSerializer[Dict[Any, Any]]()

    def register(
        self,
        data_id: DataTypeId[DataType],
        serializer: ISerializeData[DataType],
    ) -> None:
        self._serializers[data_id] = serializer

    def serialize(self, data_id: DataTypeId[DataType], data: DataType) -> str:
        return self._get_serializer(data_id).serialize(data)

    def deserialize(self, data_id: DataTypeId[DataType], data: str) -> DataType:
        return self._get_serializer(data_id).deserialize(data)

    def _get_serializer(self, data_id: DataTypeId[DataType]) -> ISerializeData[DataType]:
        # TODO: think about when we throw exceptions
        #       maybe serializers can be called with the data id and let them decide
        return self._serializers.get(data_id, self._default_serializer)
