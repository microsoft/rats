"""
This package is meant to only be used by the rats development environment.

Generally it just configures the available plugins and a similar folder can be created in other
projects in order to leverage things like our CI tooling.

It looks like a bit of a mess because it's where we deal with the mess of the rest of the project.
Hoping we'll start to find some patterns to address this as we build a few more plugins.
"""

from ._plugin import PluginContainer

__all__ = [
    "PluginContainer",
]
