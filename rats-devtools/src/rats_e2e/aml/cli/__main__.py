"""
A set of cli commands that serve as examples of how to use the `rats.aml` package.

Run this module with coverage.py: `coverage run --branch -m rats_e2e.runtime`.
"""

import logging

from rats_e2e.aml import cli

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    cli.main()
