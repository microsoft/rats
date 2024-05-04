# type: ignore
import click

from rats import cli

from ._formatter import FileFormatter, FileFormatterRequest


class PycharmCommands(cli.CommandContainer):
    @cli.command(cli.CommandId.auto())
    @click.argument(
        "filename",
        type=click.Path(exists=True, file_okay=True, dir_okay=True),
    )
    def apply_auto_formatters(self, filename: str) -> None:
        formatter = FileFormatter(request=lambda: FileFormatterRequest(filename))
        formatter.execute()
