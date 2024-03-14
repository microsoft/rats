"""
Data concepts that are not related to pipelines.

This module contains ideas about reading and writing data of different types.
"""

from abc import abstractmethod
from typing import Protocol, TypeVar

T_DataType = TypeVar("T_DataType")
Tco_DataType = TypeVar("Tco_DataType", covariant=True)
Tcontra_DataType = TypeVar("Tcontra_DataType", contravariant=True)


class IWriteData(Protocol[Tcontra_DataType]):
    @abstractmethod
    def write(self, payload: Tcontra_DataType) -> None: ...


class IReadData(Protocol[Tco_DataType]):
    @abstractmethod
    def read(self) -> Tco_DataType: ...
