from rats import projects


class TestProjectTools:
    def test_basics(self) -> None:
        tools = projects.ProjectTools(
            lambda: projects.ProjectConfig(
                name="example-project",
                path="test/rats_test_resources/projects/example-1",
                image_registry="none",
                image_push_on_build=False,
            )
        )

        assert len(tools.discover_components()) == 3

    def test_single_component_projects(self) -> None:
        tools = projects.ProjectTools(
            lambda: projects.ProjectConfig(
                name="example-project",
                path="test/rats_test_resources/projects/example-2",
                image_registry="none",
                image_push_on_build=False,
            )
        )

        assert len(tools.discover_components()) == 1
