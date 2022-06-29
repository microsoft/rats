# from base64 import b32encode
# from pickle import dumps
from typing import NamedTuple, Type

from .data_annotation import Data


def Output(**outputs: Type[Data]) -> NamedTuple:
    # name = "ra" + str(b32encode(dumps(outputs)), "utf-8").replace("=", "")
    # def represent_type(t: Type[Data]) -> str:
    #     try:
    #         return t.__name__
    #     except:
    #         return str(t)

    # name = "(" + ", ".join([f"{k}: {represent_type(v)}" for k, v in outputs.items()]) + ")"
    name = "outputs"

    return NamedTuple(name, list(outputs.items()))
