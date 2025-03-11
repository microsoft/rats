"""
Library to help with project management.

A project is loosely tied to one repository, which is made up of one or more components. Each
component is a separate entity that can be built, tested, and released independently.
"""

from ._component_tools import ComponentId, ComponentTools, UnsetComponentTools
from ._plugin import PluginContainer, PluginServices, find_repo_root
from ._project_tools import (
    ComponentNotFoundError,
    ProjectConfig,
    ProjectNotFoundError,
    ProjectTools,
)

__all__ = [
    "ComponentId",
    "ComponentNotFoundError",
    "ComponentTools",
    "PluginContainer",
    "PluginServices",
    "ProjectConfig",
    "ProjectNotFoundError",
    "ProjectTools",
    "UnsetComponentTools",
    "find_repo_root",
]
