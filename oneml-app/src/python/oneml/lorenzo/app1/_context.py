from enum import Enum, auto


class AppCommand(Enum):
    NONE = auto()
    RUN_PIPELINE = auto()
    RUN_NODE = auto()
