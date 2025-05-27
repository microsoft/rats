"""
Small module to help configure logging for rats applications.

We provide a rats application that can be executed at the beginning of your process, that will
handle configuring the python logging libraries, with a few configuration options being exposed.

!!! warning
    We expose the logging functionality through a [rats.apps.AppContainer][] in order to leverage
    the built in plugin system to give users the ability to adjust the default settings, but this
    entire application should be lightweight and should not contain very complex logic, avoiding
    logic that is very time consuming or has a chance of failing with confusing errors.

    If the logging options made available through this module are far from what is desired, instead
    of adding flags and options to this module, we recommend configuring logging in your own code.
"""

from ._app import AppConfigs, ConfigureApplication
from ._showwarning import showwarning

__all__ = [
    "AppConfigs",
    "ConfigureApplication",
    "showwarning",
]
