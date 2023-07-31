from oneml.app import OnemlApp
from oneml.processors.example._di_container import DiamondExampleDiContainer
from oneml.processors.example._pipeline import DiamondExampleServices

app = OnemlApp.default()
app.parse_service_container(DiamondExampleDiContainer(app))
print(f"running pipeline: {DiamondExampleServices.PIPELINE}")
app.run_pipeline(DiamondExampleServices.PIPELINE)
print("done running pipeline")
