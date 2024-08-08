from rats import annotations as anns
from rats import apps


class AnnotationNamespaces:
    COMMANDS = "commands"
    COMMAND_GROUPS = "command-groups"


def command(command_id: apps.ServiceId[apps.Executable] = None) -> anns.DecoratorType:
    def decorator(fn: anns.FunctionType) -> anns.FunctionType:
        c = command_id or apps.ServiceId[apps.Executable](fn.__name__.replace("_", "-").strip("-"))
        return anns.annotation("commands", c)(fn)

    return decorator


def group(command_id: apps.ServiceId[apps.Executable] = None) -> anns.DecoratorType:
    def decorator(fn: anns.FunctionType) -> anns.FunctionType:
        c = command_id or apps.ServiceId[apps.Executable](fn.__name__.replace("_", "-"))
        return anns.annotation("command-groups", c)(fn)

    return decorator


def get_class_commands(cls: type) -> anns.AnnotationsContainer:
    return anns.get_class_annotations(cls).with_namespace("commands")


def get_class_groups(cls: type) -> anns.AnnotationsContainer:
    return anns.get_class_annotations(cls).with_namespace("command-groups")
