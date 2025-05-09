"""
General purpose library to attach annotations to functions.

Annotations are typically, but not exclusively, attached using decorators.
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach_stub(__name__, __file__)  # type: ignore[reportUnknownVariableType]
