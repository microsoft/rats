"""This package provides interoperability between immunocli di and oneml di."""

"""
The di container and plugin in this package are the immunocli take on these concepts.
The package exposes a single oneml service, which is initialized by the immunocli plugin, and
not by the standard oneml service registration mechanism.
"""

from ._app_plugin import OnemlHabitatsImmunocliServices
from ._plugin import OnemlHabitatsCliPlugin

__all__ = [
    "OnemlHabitatsImmunocliServices",
    "OnemlHabitatsCliPlugin",
]
