# type: ignore[reportUntypedFunctionDecorator]
"""..."""

from typing import NamedTuple

from rats import annotations


class FruitId(NamedTuple):
    """Any named tuple can be attached to functions."""

    name: str
    color: str


def fruit(fid: FruitId) -> annotations.DecoratorType:
    """A decorator that attached a fruit object to a function."""
    return annotations.annotation("fruits", fid)


@fruit(FruitId("apple", "red"))
def some_function() -> None:
    """..."""
    pass


@fruit(FruitId("banana", "yellow"))
class SomeClass:
    """Class definitions can also be annotated."""

    @fruit(FruitId("cherry", "red"))
    def some_method(self) -> None:
        """Or class methods."""
        pass


def _example() -> None:
    """Let's define a couple objects and annotate them."""
    print(annotations.get_class_annotations(SomeClass))
    print(annotations.get_annotations(SomeClass))
    print(annotations.get_annotations(some_function))
    print(annotations.get_annotations(SomeClass.some_method))


if __name__ == "__main__":
    _example()
