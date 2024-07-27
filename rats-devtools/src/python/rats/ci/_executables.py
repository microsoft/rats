from rats import apps


class PingExecutable(apps.Executable):
    _msg: str

    def __init__(self, msg: str) -> None:
        self._msg = msg

    def execute(self) -> None:
        print(f"[{self._msg}] Ping!")


class PongExecutable(apps.Executable):
    _msg: str

    def __init__(self, msg: str) -> None:
        self._msg = msg

    def execute(self) -> None:
        print(f"[{self._msg}] Pong!")
