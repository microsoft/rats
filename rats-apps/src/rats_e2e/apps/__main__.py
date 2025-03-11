"""
A set of cli commands that serve as examples of how to use the `rats.apps` package.

Run this module with coverage.py: `coverage run --branch -m rats_e2e.runtime`.
"""

import logging

from rats import apps
from rats_e2e import apps as e2e

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    apps.run_plugin(e2e.ExampleCliApp)
