# type: ignore
import click

from rats import cli
from rats.cli._annotations import CommandContainer


class Foo(CommandContainer):
    @cli.command(cli.CommandId("foocli123"))
    def bar(self) -> None:
        print("doing bar")

    @cli.command(cli.CommandId("foocli2"))
    @click.argument("example")
    def baz(self, example: str) -> None:
        print(f"doing baz with {example}")

    @cli.command(cli.CommandId.auto())
    def auto_named_thing(self) -> None:
        print("doing auto_named_thing")


if __name__ == "__main__":
    f = Foo()

    cli = click.Group()
    f.on_group_open(cli)
    cli()
