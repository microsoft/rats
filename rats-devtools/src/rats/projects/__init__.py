"""
Library to help with project management.

A project is loosely tied to one repository, which is made up of one or more components. Each
component is a separate entity that can be built, tested, and released independently.
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach_stub(__name__, __file__)
