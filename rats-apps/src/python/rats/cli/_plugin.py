import click

from ._container import Container


def create_group(group: click.Group, container: Container) -> click.Group:
    """
    A simple shortcut to create a [click.Group][] with commands provided by `rats.cli.Container`'s.

    ```python
    import click
    from rats import cli


    class Example(cli.Container):
        @cli.command()
        def my_command(self) -> None:
            print("hello, world. run me with `my-cli my-command`.")


    if __name__ == "__main__":
        cli.create_group(click.Group("my-cli"), Example()).main()
    ```

    Args:
        group: The [click.Group][] commands will be added to.
        container: The [rats.cli.Container][] instance to attach commands from
    """
    container.attach(group)
    return group


def attach(
    group: click.Group,
    command: click.Command | click.Group,
    *commands: click.Command | click.Group,
) -> None:
    """
    Convenience function to attach multiple [click.Command]'s to a [click.Group].

    ```python
    import click
    from rats import cli

    cli.attach(
        click.Group("my-cli"),
        click.Command("command-1"),
        click.Command("command-2"),
    )
    ```

    Args:
        group: The [click.Group] we want to build.
        command: A [click.Command] to attach to the provided group.
        *commands: Any number of additional [click.Command]'s to attach.

    Returns: The input [click.Group][] with all of the commands attached.
    """
    group.add_command(command)
    for c in commands:
        group.add_command(c)
