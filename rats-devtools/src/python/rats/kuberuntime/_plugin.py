import os
from pathlib import Path
from typing import cast

import click

from rats import apps, cli
from rats import devtools as devtools
from rats import projects as projects

from ._commands import PluginCommands
from ._runtime import K8sRuntime, K8sWorkflowRun, KustomizeImage, RuntimeConfig


@apps.autoscope
class _PluginClickServices:
    GROUP = apps.ServiceId[click.Group]("group")


@apps.autoscope
class PluginServices:
    K8S_RUNTIME = apps.ServiceId[apps.Runtime]("k8s-runtime")
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    CLICK = _PluginClickServices

    @staticmethod
    def component_runtime(name: str) -> apps.ServiceId[apps.Runtime]:
        return apps.ServiceId[apps.Runtime](f"{PluginServices.K8S_RUNTIME}[{name}][runtime]")

    @staticmethod
    def component_command(name: str) -> apps.ServiceId[tuple[str, ...]]:
        return apps.ServiceId[tuple[str, ...]](f"{PluginServices.K8S_RUNTIME}[{name}][command]")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(cli.PluginServices.EVENTS.command_open(cli.PluginServices.ROOT_COMMAND))
    def _runner_cli(self) -> apps.Executable:
        def run() -> None:
            group = self._app.get(
                cli.PluginServices.click_command(cli.PluginServices.ROOT_COMMAND)
            )
            k8srunner = self._app.get(PluginServices.CLICK.GROUP)
            self._app.get(PluginServices.COMMANDS).on_group_open(k8srunner)
            group.add_command(cast(click.Command, k8srunner))

        return apps.App(run)

    @apps.service(PluginServices.CLICK.GROUP)
    def _click_group(self) -> click.Group:
        return click.Group(
            "k8s-runtime",
            help="submit executables and events to k8s",
        )

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=self._app.get(devtools.PluginServices.PROJECT_TOOLS),
            # on worker nodes, we always want the simple local runtime, for now.
            worker_node_runtime=self._app.get(apps.AppServices.STANDARD_RUNTIME),
            k8s_runtime=self._app.get(PluginServices.K8S_RUNTIME),
        )

    @apps.service(PluginServices.K8S_RUNTIME)
    def _k8s_runtime(self) -> apps.Runtime:
        try:
            return self._app.get(PluginServices.component_runtime(Path().resolve().name))
        except apps.ServiceNotFoundError as e:
            if e.service_id == PluginServices.component_runtime(Path().resolve().name):
                # this api is confusing
                return apps.NullRuntime()
            raise

    @apps.service(PluginServices.component_runtime("rats-devtools"))
    def _devtools_runtime(self) -> K8sRuntime:
        return self._k8s_component_runtime("rats-devtools")

    @apps.service(PluginServices.component_runtime("rats-examples-minimal"))
    def _minimal_runtime(self) -> K8sRuntime:
        return self._k8s_component_runtime("rats-examples-minimal")

    @apps.service(PluginServices.component_command("rats-examples-datasets"))
    def _datasets_command(self) -> tuple[str, ...]:
        return ".venv/bin/python", "-m", "rats.exampledatasets"

    @apps.service(PluginServices.component_command("rats-devtools"))
    def _devtools_command(self) -> tuple[str, ...]:
        return "rats-devtools", "k8s-runtime", "worker-node"

    @apps.service(PluginServices.component_command("rats-examples-minimal"))
    def _minimal_command(self) -> tuple[str, ...]:
        return "python", "-m", "rats.minis"

    @apps.service(PluginServices.component_runtime("rats-examples-datasets"))
    def _datasets_runtime(self) -> K8sRuntime:
        return self._k8s_component_runtime("rats-examples-datasets")

    def _k8s_component_runtime(self, name: str) -> K8sRuntime:
        def _container_images() -> tuple[KustomizeImage, ...]:
            reg = os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local")
            project_tools = self._app.get(devtools.PluginServices.PROJECT_TOOLS)
            context_hash = project_tools.image_context_hash()
            return (
                KustomizeImage(
                    "rats-devtools",
                    f"{reg}/rats-devtools",
                    context_hash,
                ),
                KustomizeImage(
                    "rats-examples-minimal",
                    f"{reg}/rats-examples-minimal",
                    context_hash,
                ),
                KustomizeImage(
                    "rats-examples-datasets",
                    f"{reg}/rats-examples-datasets",
                    context_hash,
                ),
            )

        def _factory(
            id: str,
            exe_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
            group_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
        ) -> K8sWorkflowRun:
            return K8sWorkflowRun(
                devops_component=self._app.get(devtools.PluginServices.DEVTOOLS_COMPONENT_OPS),
                main_component=self._app.get(devtools.PluginServices.component_ops(name)),
                main_component_id=projects.ComponentId(name),
                k8s_config_context=os.environ.get("DEVTOOLS_K8S_CONFIG_CONTEXT", "default"),
                container_images=_container_images(),
                command=self._app.get(PluginServices.component_command(name)),
                id=id,
                exe_ids=exe_ids,  # type: ignore
                group_ids=group_ids,  # type: ignore
            )

        return K8sRuntime(
            config=lambda: RuntimeConfig(
                id=os.environ.get("DEVTOOLS_K8S_CONTEXT_ID", "/"),
                command=("rats-devtools", "k8s-runtime", "worker-node"),
                container_images=_container_images(),
                main_component=projects.ComponentId(name),
            ),
            factory=_factory,  # type: ignore
        )
