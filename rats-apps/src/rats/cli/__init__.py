"""Use `rats.cli` to streamline the creation of CLI commands written with Click."""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach_stub(__name__, __file__)  # type: ignore[reportUnknownVariableType]
