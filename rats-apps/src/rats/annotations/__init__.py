"""
General purpose library to attach annotations to functions.

Annotations are typically, but not exclusively, attached using decorators.
"""

from ._functions import (
    AnnotationsContainer,
    DecoratorType,
    GroupAnnotations,
    T_GroupType,
    annotation,
    get_annotations,
    get_class_annotations,
)

__all__ = [
    "AnnotationsContainer",
    "DecoratorType",
    "GroupAnnotations",
    "T_GroupType",
    "annotation",
    "get_annotations",
    "get_class_annotations",
]
