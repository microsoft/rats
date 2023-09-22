from typing import Iterable, Protocol

from oneml.pipelines.dag import PipelineNode
from oneml.services import ContextProvider, IExecutable


class OnemlIoPlugin(Protocol):
    """
    Plugin class to implement when wanting to enhance the IO capabilitiesa of OneML Pipelines.

    The methods in this class are not abstract because we want to be able to add methods without
    implementors having to implement them immediately. The default implementation of each method
    will always be some form of no-op, most likely an empty method.

    Because of the above, implementors should avoid implementing this class alongside other public
    methods, because we don't want to cause conflicts with future methods. However, adding a method
    to this interface should still be considered an API breaking change, because we can't guarantee
    that our users have followed this spoken rule.
    """

    def on_node_completion(self, node: PipelineNode) -> None:
        """"""


class OnemlIoOnNodeCompletion(IExecutable):
    _node_ctx: ContextProvider[PipelineNode]
    _plugins: Iterable[OnemlIoPlugin]

    def __init__(
        self,
        node_ctx: ContextProvider[PipelineNode],
        plugins: Iterable[OnemlIoPlugin],
    ) -> None:
        self._node_ctx = node_ctx
        self._plugins = plugins

    def execute(self) -> None:
        for plugin in self._plugins:
            plugin.on_node_completion(self._node_ctx())
