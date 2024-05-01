from typing import Any

import click


class ProgrammaticExecutionGroup(click.Group):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Alias for :meth:`main`."""
        return self.main(*args, standalone_mode=False, **kwargs)


class ProgrammaticExecutionCommand(click.Command):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Alias for :meth:`main`."""
        return self.main(*args, standalone_mode=False, **kwargs)
