"""
This package exposes classes to create and use the app plugin system.

This package does not hold any actual plugins, just the concepts!
"""

from ._app import App
from ._plugin import AppPlugin, InitializePluginsExe
from ._plugin_entry_points import AppEntryPointPluginRelay, AppPluginEntryPoint

__all__ = [
    # _app
    "App",
    # _plugin_entry_points
    "AppEntryPointPluginRelay",
    "AppPlugin",
    "AppPluginEntryPoint",
    # _plugin
    "InitializePluginsExe",
]
