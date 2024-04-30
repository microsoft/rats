import click

from rats import apps


@apps.autoscope
class PluginGroups:
    @staticmethod
    def command(name: str) -> apps.ServiceId[click.Command]:
        return apps.ServiceId(f"cli-commands[{name}]")


@apps.autoscope
class PluginServices:
    GROUPS = PluginGroups
