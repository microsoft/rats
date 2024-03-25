from oneml.services import IExecutable, ServiceId, scoped_service_ids


@scoped_service_ids
class _RatsAppServiceGroups:
    # COMMANDS = ServiceId[ClickCommandRegistry]("commands")
    pass


@scoped_service_ids
class RatsAppServices:
    CLI = ServiceId[IExecutable]("cli")
    GROUPS = _RatsAppServiceGroups
