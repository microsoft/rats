from unittest.mock import Mock

from rats.apps import Container, ServiceId
from rats.command_tree import CommandServiceTree, CommandTree


def test_command_service_tree_to_command_tree_no_children_no_handler():
    # Create a CommandServiceTree with no children and no handler
    command_service_tree = CommandServiceTree(
        name="test_command",
        description="Test command description",
    )

    # Create a mock container
    container = Mock(spec=Container)

    # Convert to CommandTree
    command_tree = command_service_tree.to_command_tree(container)

    # Assertions
    assert isinstance(command_tree, CommandTree)
    assert command_tree.name == "test_command"
    assert command_tree.description == "Test command description"
    assert command_tree.children == ()
    assert command_tree.kwargs_class is None
    assert command_tree.handler is None


def test_command_service_tree_to_command_tree_with_children_with_handler():
    # Create a CommandServiceTree with children and a handler
    child_service_id = ServiceId("child_command_service")
    handler_service_id = ServiceId("handler_service")
    command_service_tree = CommandServiceTree(
        name="parent_command",
        description="Parent command description",
        children=child_service_id,
        handler=handler_service_id,
    )

    # Create a mock container
    container = Mock(spec=Container)
    child_command_tree = CommandTree(name="child_command", description="Child command description")
    container.get_group.return_value = [child_command_tree]
    container.get.return_value = lambda: None

    # Convert to CommandTree
    command_tree = command_service_tree.to_command_tree(container)

    # Assertions
    assert isinstance(command_tree, CommandTree)
    assert command_tree.name == "parent_command"
    assert command_tree.description == "Parent command description"
    assert command_tree.children == (child_command_tree,)
    assert command_tree.kwargs_class is None
    assert command_tree.handler is not None
    assert callable(command_tree.handler)


def test_command_service_tree_to_command_tree_with_kwargs_class():
    # Create a CommandServiceTree with a kwargs_class
    kwargs_class = Mock()
    command_service_tree = CommandServiceTree(
        name="command_with_args",
        description="Command with arguments description",
        kwargs_class=kwargs_class,
    )

    # Create a mock container
    container = Mock(spec=Container)

    # Convert to CommandTree
    command_tree = command_service_tree.to_command_tree(container)

    # Assertions
    assert isinstance(command_tree, CommandTree)
    assert command_tree.name == "command_with_args"
    assert command_tree.description == "Command with arguments description"
    assert command_tree.children == ()
    assert command_tree.kwargs_class == kwargs_class
    assert command_tree.handler is None
