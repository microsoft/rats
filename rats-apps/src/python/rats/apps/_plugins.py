import warnings
from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

T_PluginType = TypeVar("T_PluginType")


class PluginRunner(Generic[T_PluginType]):
    """Client to apply a function to a list of plugins."""

    _plugins: Iterator[T_PluginType]

    def __init__(self, plugins: Iterator[T_PluginType]) -> None:
        self._plugins = plugins

    def apply(self, handler: Callable[[T_PluginType], None]) -> None:
        warnings.warn(
            "PluginRunner is deprecated. Use PluginContainer instances instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        for plugin in self._plugins:
            handler(plugin)
