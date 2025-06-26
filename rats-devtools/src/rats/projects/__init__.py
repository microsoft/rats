"""
Interact with the various components in the repository during development.

A project is loosely tied to one repository, which is made up of one or more components. Each
component is a separate entity that can be built, tested, and released independently. This module
provides a handful of convenience APIs to query for project and component information, along with
exposing a few methods to run commands within the context of a component's development environment.
It's common for python environments to be misconfigured, and as we run commands in multiple
components, it's easy to accidentally run commands in a component with the wrong virtual
environment being activated, with unpredictable results. The libraries in this module try to
alleviate some of these pain points while trying to remain agnostic of env management tools and
other component specific choices.

!!! warning
    Python environments are never trivial to manage, and are a common source of complexity because
    of the many ways to define your development environment. We've tested the functionality in this
    module heavily for the set of tools we use to develop rats, but some of the contained
    functionality might not work fully within components that use a different set of tool, like
    [conda](https://docs.conda.io/).
"""

from ._component_tools import ComponentId, ComponentTools, UnsetComponentTools
from ._plugin import (
    PluginConfigs,
    PluginContainer,
    PluginServices,
    find_nearest_component,
    find_repo_root,
)
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
    "PluginConfigs",
    "PluginContainer",
    "PluginServices",
    "ProjectConfig",
    "ProjectNotFoundError",
    "ProjectTools",
    "UnsetComponentTools",
    "find_nearest_component",
    "find_repo_root",
]
