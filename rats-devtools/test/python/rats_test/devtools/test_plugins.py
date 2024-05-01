from typing import Any

from rats.devtools._plugins import PluginRunner


def test_plugin_runner_apply() -> None:
    # Mock plugin and handler
    class MockPlugin:
        def __init__(self, name: str):
            self.name = name
            self.handled = False

        def handle(self):
            self.handled = True

    mock_plugins = [MockPlugin("plugin1"), MockPlugin("plugin2")]
    plugin_runner = PluginRunner(iter(mock_plugins))

    # Define a handler that calls the 'handle' method of the plugin
    def handler(plugin: MockPlugin) -> None:
        plugin.handle()

    # Apply the handler to the plugins
    plugin_runner.apply(handler)

    # Assert that each plugin was handled
    for plugin in mock_plugins:
        assert plugin.handled, f"{plugin.name} was not handled"


def test_plugin_runner_no_plugins() -> None:
    # Empty iterator of plugins
    plugin_runner = PluginRunner(iter([]))

    # Define a handler that should never be called
    handler_called = False

    def handler(plugin: Any) -> None:
        nonlocal handler_called
        handler_called = True

    # Apply the handler to the plugins
    plugin_runner.apply(handler)

    # Assert that the handler was never called
    assert not handler_called, "Handler was called on an empty iterator of plugins"
from rats.devtools._command_tree import get_attribute_docstring


def test_get_attribute_docstring():
    @dataclass
    class MockDataclass:
        """
        MockDataclass description.
        """
        field: int
        """The field's docstring."""

    docstring = get_attribute_docstring(MockDataclass, 'field')
    assert docstring == "The field's docstring.", "The docstring did not match the expected value"


def test_get_attribute_docstring_no_docstring():
    @dataclass
    class MockDataclass:
        field: int

    docstring = get_attribute_docstring(MockDataclass, 'field')
    assert docstring == "", "The docstring should be empty for a field without a docstring"


def test_get_attribute_docstring_nonexistent_field():
    @dataclass
    class MockDataclass:
        field: int

    with pytest.raises(ValueError) as exc_info:
        get_attribute_docstring(MockDataclass, 'nonexistent_field')
    assert "Attribute nonexistent_field not found in dataclass MockDataclass" in str(exc_info.value), "The error message did not match the expected value"
