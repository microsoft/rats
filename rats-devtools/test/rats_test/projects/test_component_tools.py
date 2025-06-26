import subprocess
from pathlib import Path

from rats import projects


class TestComponentTools:
    def test_basics(self) -> None:
        tools = projects.ProjectTools(
            lambda: projects.ProjectConfig(
                name="example-project",
                path="test/rats_test_resources/projects/example-1",
                image_registry="none",
                image_push_on_build=False,
            )
        )

        examples = [
            "pdm",
            "poetry",
            "uv",
            "nested-uv",
        ]
        for x in examples:
            component = tools.get_component(f"example-{x}")
            assert component.component_name() == f"example-{x}"

    def test_nested(self) -> None:
        tools = projects.ProjectTools(
            lambda: projects.ProjectConfig(
                name="example-project",
                path="test/rats_test_resources/projects/example-1",
                image_registry="none",
                image_push_on_build=False,
            )
        )
        component = tools.get_component("example-nested-uv")
        readme_path = component.find_path("README.md")
        expected = Path(
            "test/rats_test_resources/projects/example-1/nested/example-nested-uv/README.md",
        ).resolve()
        assert str(readme_path) == str(expected)

    def test_executing_uv(self) -> None:
        tools = projects.ProjectTools(
            lambda: projects.ProjectConfig(
                name="example-project",
                path="test/rats_test_resources/projects/example-1",
                image_registry="none",
                image_push_on_build=False,
            )
        )

        examples = [
            "poetry",
            "uv",
            "nested-uv",
        ]
        for x in examples:
            component = tools.get_component(f"example-{x}")

            cmd = [
                "env",
                "-u",
                "UV_ACTIVE",
                "-u",
                "VIRTUAL_ENV",
                "uv",
                "run",
                "python",
                "-m",
                component.component_name().replace("-", "_"),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=component.find_path("."))
            assert result.stdout.strip() == f"hello, world! example-1/{component.component_name()}"

    def test_executing_poetry(self) -> None:
        tools = projects.ProjectTools(
            lambda: projects.ProjectConfig(
                name="example-project",
                path="test/rats_test_resources/projects/example-1",
                image_registry="none",
                image_push_on_build=False,
            )
        )

        component = tools.get_component("example-poetry")

        cmd = [
            "env",
            "-u",
            "POETRY_ACTIVE",
            "-u",
            "VIRTUAL_ENV",
            "poetry",
            "run",
            "python",
            "-m",
            "example_poetry",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=component.find_path("."))
        assert result.stdout.strip() == "hello, world! example-1/example-poetry"
