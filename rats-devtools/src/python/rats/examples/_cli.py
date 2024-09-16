from rats import cli


class PluginCommands(cli.CommandContainer):
    @cli.command()
    def _ping(self) -> None:
        print("ping")

    @cli.command()
    def _pong(self) -> None:
        print("pong")
