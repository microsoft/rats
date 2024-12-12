from rats import projects


class TestComponentTools:
    def test_basics(self) -> None:
        tools = projects.ProjectTools(
            lambda: projects.ProjectConfig(
                name="example-project",
                path="test/resources/projects",
                image_registry="none",
                image_push_on_build=False,
            )
        )

        examples = ["pdm", "poetry", "uv"]
        for x in examples:
            component = tools.get_component(f"example-{x}")
            assert component.component_name() == f"example-{x}"
