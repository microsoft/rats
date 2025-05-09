"""Small package to help configure logging for rats applications."""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach_stub(__name__, __file__)  # type: ignore[reportUnknownVariableType]
