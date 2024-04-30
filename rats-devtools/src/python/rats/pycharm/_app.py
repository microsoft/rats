import click

from rats import apps, devtools  # type: ignore[reportAttributeAccessIssue]
from rats.pycharm._formatter import FileFormatter, FileFormatterRequest


@apps.autoscope
class PluginGroups:
    @staticmethod
    def command(name: str) -> apps.ServiceId[click.Command]:
        return apps.ServiceId(f"cli-commands[{name}]")


@apps.autoscope
class PluginServices:
    CLI = apps.ServiceId[apps.Executable]("cli")
    GROUPS = PluginGroups


#
# class RatsPycharmGroups:
#     COMMANDS = apps.ServiceId[devtools.ClickCommandRegistry]("pycharm-commands")


class RatsPycharmPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.AppServices.GROUPS.CLI_ROOT_COMMANDS)
    def pycharm_command(self) -> click.Command:
        provider = devtools.CommandProvider(
            command_names=frozenset(["apply-auto-formatters"]),
            service_mapper=lambda name: PluginServices.GROUPS.command(name),
            container=self,
        )

        return devtools.LazyClickGroup(
            name="pycharm",
            provider=provider,
        )

    @apps.service(PluginServices.GROUPS.command("apply-auto-formatters"))
    def apply_auto_formatters(self) -> click.Command:
        @click.argument(
            "filename",
            type=click.Path(exists=True, file_okay=True, dir_okay=False),
        )
        def run(filename: str) -> None:
            formatter = FileFormatter(request=lambda: FileFormatterRequest(filename))
            formatter.execute()

        return click.Command(
            name="apply-auto-formatters",
            callback=run,
            params=list(reversed(getattr(run, "__click_params__", []))),
            help="Help for apply-auto-formatters",
            short_help="Short help for apply-auto-formatters",
        )
