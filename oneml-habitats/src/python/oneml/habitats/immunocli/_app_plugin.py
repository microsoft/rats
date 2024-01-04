import logging

from oneml.services import ServiceId, scoped_service_ids

from ._locate_habitats_cli_di_container import ILocateHabitatsCliDiContainer

logger = logging.getLogger(__name__)


# The single service we expose is initialized by immunocli plugin, so there is no need to have
# a oneml di container and plugin.
# If we ever need to expose more services, we can add a oneml di container and plugin.


@scoped_service_ids
class OnemlHabitatsImmunocliServices:
    LOCATE_HABITATS_CLI_DI_CONTAINERS = ServiceId[ILocateHabitatsCliDiContainer](
        "locate-habitats-cli-di-containers"
    )
