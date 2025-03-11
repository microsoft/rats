from rats import projects


class TestProjectTools:
    def test_basics(self) -> None:
        tools = projects.ProjectTools(
            lambda: projects.ProjectConfig(
                name="example-project",
                path="test/resources/projects",
                image_registry="none",
                image_push_on_build=False,
            )
        )

        assert len(tools.discover_components()) == 3
