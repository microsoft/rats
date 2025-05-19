from typing import Any, NamedTuple

from rats import app_context


class Request(NamedTuple):
    app_ids: tuple[str, ...]
    """The app ids being run by [rats.runtime.Application][]."""

    context: app_context.Collection[Any]
    """The [rats.app_context.Collection][] that was submitted and made available to executed apps."""


class RequestNotFoundError(RuntimeError):
    """Thrown if [rats.runtime.AppServices.REQUEST][] is accessed without the application being run."""

    def __init__(self) -> None:
        super().__init__("no running runtime request found.")


class DuplicateRequestError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("request already executed.")
