from rats.app import RatsApp
from rats.processors._legacy_subpackages.example._app_plugin import (
    DiamondExampleDiContainer,
    DiamondExampleServices,
)

app = RatsApp.default()
app.parse_service_container(DiamondExampleDiContainer(app))
print(f"running pipeline: {DiamondExampleServices.DIAMOND_EXECUTABLE}")
app.run_pipeline(DiamondExampleServices.DIAMOND_EXECUTABLE)
print("done running pipeline")
