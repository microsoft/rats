from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    """Wraps the information of a cli command."""

    cwd: str
    """
    The directory the command is run from.

    Often taken from [pathlib.Path.cwd][] and turned into a plain string.
    """
    argv: tuple[str, ...]
    """
    The list of cli arguments passed to the command.

    This has the same meaning as [sys.argv][] and is often populated by it.
    """
    env: Mapping[str, str]
    """
    The process environment variables often populated by [os.environ][].
    """
