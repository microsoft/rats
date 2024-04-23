from typing import Any, TypedDict


class AOutput(TypedDict):
    z1: float
    z2: float


class BOutput(TypedDict):
    z: float


class COutput(TypedDict):
    z: float


class DOutput(TypedDict):
    z1: float
    z2: float


class A:
    def process(self) -> AOutput:
        return {"z1": 1.0, "z2": 2.0}


class B:
    def process(self, x: Any) -> BOutput:
        return {"z": 3.0}


class C:
    def process(self, x: Any) -> COutput:
        return {"z": 4.0}


class D:
    def process(self, x1: Any, x2: Any) -> DOutput:
        print(f"x1={x1}, x2={x2}")
        return {"z1": x1, "z2": x2}
