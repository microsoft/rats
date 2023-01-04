from abc import abstractmethod
from argparse import ArgumentParser
from typing import Any, Optional, Protocol, Sequence


class SubParsersAction(Protocol):
    # This protocol is needed because we need to typehint for the argparse._SubParsersAction class
    # https://github.com/python/cpython/issues/85758#issuecomment-1320520553
    @abstractmethod
    def add_parser(
        self,
        name: str,
        *,
        help: Optional[str] = ...,
        aliases: Sequence[str] = ...,
        prog: Optional[str] = ...,
        usage: Optional[str] = ...,
        description: Optional[str] = ...,
        epilog: Optional[str] = ...,
        parents: Sequence[ArgumentParser] = ...,
        formatter_class: Any = ...,
        prefix_chars: str = ...,
        fromfile_prefix_chars: Optional[str] = ...,
        argument_default: Any = ...,
        conflict_handler: str = ...,
        add_help: bool = ...,
        allow_abbrev: bool = ...,
        exit_on_error: bool = ...,
    ) -> ArgumentParser:
        pass
