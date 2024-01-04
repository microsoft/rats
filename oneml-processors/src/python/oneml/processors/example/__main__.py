from oneml.app import OnemlApp
from oneml.processors.example._app_plugin import DiamondExampleDiContainer, DiamondExampleServices

app = OnemlApp.default()
app.parse_service_container(DiamondExampleDiContainer(app))
print(f"running pipeline: {DiamondExampleServices.DIAMOND_EXECUTABLE}")
app.run_pipeline(DiamondExampleServices.DIAMOND_EXECUTABLE)
print("done running pipeline")
