# type: ignore

from rats import cli


class PycharmCommands(cli.CommandContainer):
    @cli.command(cli.CommandId.auto())
    def apply_auto_formatters(self) -> None:
        print("doing bar")
