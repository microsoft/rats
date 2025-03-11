"""We try to submit executables as AML jobs."""

import warnings
from textwrap import dedent

from ._plugin import PluginServices
from ._runtime import AmlEnvironment, AmlIO, AmlRuntime, AmlWorkspace, RuntimeConfig

deprecation_msg = dedent("""
    the rats.amlruntime module is deprecated.
    the rats.aml module will be replacing its functionality over the coming releases.
    https://microsoft.github.io/rats/rats-devtools/rats.aml/
""")

warnings.warn(deprecation_msg, DeprecationWarning, stacklevel=2)

__all__ = [
    "AmlEnvironment",
    "AmlIO",
    "AmlRuntime",
    "AmlWorkspace",
    "PluginServices",
    "RuntimeConfig",
]
