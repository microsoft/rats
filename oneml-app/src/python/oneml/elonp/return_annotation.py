import logging
from typing import Type, Any, Protocol, runtime_checkable
from types import new_class
from pickle import dumps
from base64 import b32encode

logger = logging.getLogger(__name__)

def return_annotation(**kwds: Type) -> Type:
    name = "ra"+str(b32encode(dumps(kwds)), 'utf-8').replace("=","")
    def getitem(self, key: str) -> Any:
        ...
    def clsexec(ns):
        ns["__annotations__"] = kwds
        ns["__getitem__"] = getitem
    cls = runtime_checkable(
        new_class(
            name,
            bases=(Protocol,),
            exec_body=clsexec))
    return cls
