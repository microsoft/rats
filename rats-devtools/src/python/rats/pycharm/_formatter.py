import subprocess
import sys
from pathlib import Path

from typing_extensions import NamedTuple

from rats import apps


class FileFormatterRequest(NamedTuple):
    filename: str


class FileFormatter(apps.Executable):
    _request: apps.ConfigProvider[FileFormatterRequest]

    def __init__(self, request: apps.ConfigProvider[FileFormatterRequest]) -> None:
        self._request = request

    def execute(self) -> None:
        req = self._request()
        filename = req.filename

        if filename.startswith("src/"):
            # only other place this command is allowed is in the devtools component.
            component_path = Path()
            relative_file = filename
            pyproject_path = Path("pyproject.toml")
        else:
            component_path = Path(filename.split("/")[0])
            relative_file = "/".join(filename.split("/")[1:])
            pyproject_path = Path(f"{component_path}/pyproject.toml")

        if not pyproject_path.is_file():
            raise ValueError("does not seem to be running within repo root")

        poetry_commands = [
            ["ruff", "check", "--fix", "--unsafe-fixes", str(relative_file)],
            ["ruff", "format", str(relative_file)],
        ]

        try:
            for cmd in poetry_commands:
                subprocess.run(
                    ["poetry", "run", *cmd],
                    check=True,
                    cwd=component_path,
                )
        except subprocess.CalledProcessError:
            # We exit successfully so pycharm doesn't auto-disable our hook :(
            sys.exit(0)
