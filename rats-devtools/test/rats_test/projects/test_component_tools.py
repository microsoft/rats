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
