import subprocess
import sys
from pathlib import Path

import click

from rats import devtools


class RatsCiCommands(devtools.ClickCommandRegistry):
    @devtools.command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def check_all(self, component_path: str) -> None:
        """If this command passes, ci should pass.

        I hope.
        """
        pyproject_path = Path(f"{component_path}/pyproject.toml")

        if not pyproject_path.is_file():
            raise ValueError("does not seem to be running within repo root")

        poetry_commands = [
            ["ruff", "check", "--fix", "--unsafe-fixes"],
            ["ruff", "format", "--check"],
            ["pyright"],
            ["pytest"],
        ]

        try:
            for cmd in poetry_commands:
                subprocess.run(
                    ["poetry", "run", *cmd],
                    check=True,
                    cwd=component_path,
                )
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @devtools.command
    def ping(self) -> None:
        """No-op used for testing."""
        print("pong")
