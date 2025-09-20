from rats import apps


class Lifecycle(apps.Executable):
    _prepare: apps.Executable
    _submit: apps.Executable
    _monitor: apps.Executable

    def __init__(
        self,
        prepare: apps.Executable,
        submit: apps.Executable,
        monitor: apps.Executable,
    ) -> None:
        self._prepare = prepare
        self._submit = submit
        self._monitor = monitor

    def execute(self) -> None:
        self._prepare.execute()
        self._submit.execute()
        self._monitor.execute()
