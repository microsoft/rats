"""
Library to help with project management.

A project is loosely tied to one repository, which is made up of one or more components. Each
component is a separate entity that can be built, tested, and released independently.
"""

from ._component_tools import ComponentId, ComponentTools, UnsetComponentTools
from ._plugin import PluginContainer, PluginServices, find_repo_root
from ._project_tools import ComponentNotFoundError, ProjectNotFoundError, ProjectTools

__all__ = [
    "ComponentId",
    "PluginServices",
    "PluginContainer",
    "ComponentTools",
    "UnsetComponentTools",
    "ProjectTools",
    "ComponentNotFoundError",
    "ProjectNotFoundError",
    "find_repo_root",
]
