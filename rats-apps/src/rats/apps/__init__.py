"""
Libraries to help create applications with a strong focus on composability and testability.

Applications give you the ability to define a development experience to match your project's
domain.
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach_stub(__name__, __file__)  # type: ignore[reportUnknownVariableType]
