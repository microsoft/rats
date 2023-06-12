from oneml.services import ServiceId, scoped_service_ids

from ._locate_habitats_cli_di_container import ILocateHabitatsCliDiContainer


@scoped_service_ids
class OnemlHabitatsServices:
    LOCATE_HABITATS_CLI_DI_CONTAINERS = ServiceId[ILocateHabitatsCliDiContainer]("locate-habitats-cli-di-containers")
