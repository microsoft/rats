from .processor import Processor


def processor(cls: type) -> type:
    if Processor in cls.__mro__:
        raise TypeError(
            f"Do not list <Processor> as a base class when decorating a class using the "
            f"<processor> decorator.  The decorator will do it for you."
        )

    clsname = cls.__name__
    bases = (cls, Processor)
    return type(clsname, bases, {})
