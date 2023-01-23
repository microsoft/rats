from oneml.pipelines.context._client import ContextClient, IManageExecutionContexts
from oneml.pipelines.session import PipelineSessionClient
from oneml.pipelines.settings import PipelineSettingsClient


class PipelineBuilderFactory:
    def pipeline_session_context(self) -> IManageExecutionContexts[PipelineSessionClient]:
        return ContextClient()

    def pipeline_settings(self) -> PipelineSettingsClient:
        return PipelineSettingsClient()
