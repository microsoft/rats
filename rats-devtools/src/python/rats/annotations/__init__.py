"""
General purpose library to attach annotations to functions.

Annotations are typically, but not exclusively, attached using decorators.
"""

from ._functions import FunctionAnnotations, FunctionAnnotationsBuilder
from ._groups import GroupAnnotations, T_GroupType

__all__ = [
    "GroupAnnotations",
    "T_GroupType",
    "FunctionAnnotations",
    "FunctionAnnotationsBuilder",
]
