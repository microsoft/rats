"""We try to submit executables as AML jobs."""

import warnings
from textwrap import dedent

import lazy_loader

deprecation_msg = dedent("""
    the rats.amlruntime module is deprecated.
    the rats.aml module will be replacing its functionality over the coming releases.
    https://microsoft.github.io/rats/rats-devtools/rats.aml/
""")

warnings.warn(deprecation_msg, DeprecationWarning, stacklevel=2)


__getattr__, __dir__, __all__ = lazy_loader.attach_stub(__name__, __file__)
