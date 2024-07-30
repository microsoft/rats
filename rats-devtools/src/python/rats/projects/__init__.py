"""
Library to help with project management.

A project is loosely tied to one repository, which is made up of one or more components. Each
component is a separate entity that can be built, tested, and released independently.
"""

from ._components import ComponentId, ComponentOperations, UnsetComponentOperations
from ._plugin import PluginContainer, PluginServices
from ._tools import ComponentNotFoundError, ProjectNotFoundError, ProjectTools

__all__ = [
    "ComponentId",
    "PluginServices",
    "PluginContainer",
    "ComponentOperations",
    "UnsetComponentOperations",
    "ProjectTools",
    "ComponentNotFoundError",
    "ProjectNotFoundError",
]
