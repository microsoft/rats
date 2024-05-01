import pytest
from rats.devtools._plugins import PluginRunner


def test_plugin_runner_apply():
    # Mock plugin and handler
    class MockPlugin:
        def __init__(self, name):
            self.name = name
            self.handled = False

        def handle(self):
            self.handled = True

    mock_plugins = [MockPlugin("plugin1"), MockPlugin("plugin2")]
    plugin_runner = PluginRunner(mock_plugins)

    # Define a handler that calls the 'handle' method of the plugin
    def handler(plugin):
        plugin.handle()

    # Apply the handler to the plugins
    plugin_runner.apply(handler)

    # Assert that each plugin was handled
    for plugin in mock_plugins:
        assert plugin.handled, f"{plugin.name} was not handled"


def test_plugin_runner_no_plugins():
    # Empty iterator of plugins
    plugin_runner = PluginRunner(iter([]))

    # Define a handler that should never be called
    handler_called = False

    def handler(plugin):
        nonlocal handler_called
        handler_called = True

    # Apply the handler to the plugins
    plugin_runner.apply(handler)

    # Assert that the handler was never called
    assert not handler_called, "Handler was called on an empty iterator of plugins"
