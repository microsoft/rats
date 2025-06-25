import tempfile
from collections.abc import Callable
from pathlib import Path

import pytest

from rats import projects


class TestProjectTools:
    def test_basics(self) -> None:
        tools = projects.ProjectTools(self._project_config("example-1"))
        assert len(tools.discover_components()) == 4

    def test_single_component_projects(self) -> None:
        tools = projects.ProjectTools(self._project_config("example-2"))
        assert len(tools.discover_components()) == 1

    def test_pyproject_directory(self) -> None:
        tools = projects.ProjectTools(self._project_config("example-3"))
        assert len(tools.discover_components()) == 0

    def test_repo_root(self) -> None:
        tools = projects.ProjectTools(self._project_config("example-1"))
        tools_root = str(tools.repo_root().resolve())
        expected = str(Path("test/rats_test_resources/projects/example-1").resolve())
        assert tools_root == expected

        with tempfile.TemporaryDirectory() as tmpdir:
            bad_tools = projects.ProjectTools(
                lambda: projects.ProjectConfig(
                    name="example-project",
                    path=tmpdir,
                    image_registry="none",
                    image_push_on_build=False,
                )
            )
            with pytest.raises(projects.ProjectNotFoundError):
                bad_tools.repo_root()

    def test_invalid_components(self) -> None:
        tools = projects.ProjectTools(self._project_config("example-1"))
        with pytest.raises(projects.ComponentNotFoundError):
            tools.get_component("does-not-exist")

    def test_project_name(self) -> None:
        tools = projects.ProjectTools(self._project_config("example-1"))
        assert tools.project_name() == "example-project"

    def _project_config(self, name: str) -> Callable[[], projects.ProjectConfig]:
        return lambda: projects.ProjectConfig(
            name="example-project",
            path=f"test/rats_test_resources/projects/{name}",
            image_registry="none",
            image_push_on_build=False,
        )
