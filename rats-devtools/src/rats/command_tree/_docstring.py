import inspect
import re
from dataclasses import fields, is_dataclass


def get_attribute_docstring(dataclass_tpe: type, field_name: str) -> str:
    """
    Get the docstring of the attribute from the dataclass.

    Args:
        dataclass_tpe: The dataclass type.
        field_name: The name of the field.

    Returns:
        The docstring of the attribute if present, otherwise an empty string.

    Raises:
        ValueError: If the attribute is not found in the dataclass.
    """
    mro = inspect.getmro(dataclass_tpe)
    assert is_dataclass(mro[0])
    assert mro[-1] is object
    mro = mro[:-1]

    for base_class in mro:
        if is_dataclass(base_class):
            for field in fields(base_class):
                if field.name == field_name:
                    source = inspect.getsource(base_class)

                    attribute_definition = re.search(rf"{field.name}\s*:", source)
                    assert attribute_definition is not None

                    try:
                        docstring_start = source.index('"""', attribute_definition.end())
                        docstring_end = source.index('"""', docstring_start + 3)

                        return source[docstring_start + 3 : docstring_end]
                    except ValueError:
                        return ""

    raise ValueError(
        f"Attribute {field_name} not found in dataclass {dataclass_tpe.__module__}.{dataclass_tpe.__qualname__}"  # noqa: E501
    )
