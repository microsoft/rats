from rats import apps

from ._runtime import RuntimeConfig


@apps.autoscope
class _PluginConfigs:
    AML_RUNTIME = apps.ServiceId[RuntimeConfig]("aml-runtime")
    EXE_GROUP = apps.ServiceId[apps.ServiceId[apps.Executable]]("exe-group")

    @staticmethod
    def component_runtime(name: str) -> apps.ServiceId[RuntimeConfig]:
        return apps.ServiceId[RuntimeConfig](f"{_PluginConfigs.AML_RUNTIME.name}[{name}][runtime]")


@apps.autoscope
class PluginServices:
    AML_RUNTIME = apps.ServiceId[apps.Runtime]("aml-runtime")
    AML_CLIENT = apps.ServiceId["MLClient"]("aml-client")  # type: ignore[reportUndefinedVariable]
    AML_ENVIRONMENT_OPS = apps.ServiceId["EnvironmentOperations"]("aml-environment-ops")  # type: ignore[reportUndefinedVariable]
    AML_JOB_OPS = apps.ServiceId["JobOperations"]("aml-job-ops")  # type: ignore[reportUndefinedVariable]

    CONFIGS = _PluginConfigs

    @staticmethod
    def component_runtime(name: str) -> apps.ServiceId[apps.Runtime]:
        return apps.ServiceId[apps.Runtime](f"{PluginServices.AML_RUNTIME.name}[{name}]")
