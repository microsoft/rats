import logging
import sys
import warnings
from pathlib import Path

logger = logging.getLogger(__name__)


def showwarning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: str | None = None,
    line: str | None = None,
) -> None:
    """
    Handler that logs warnings using the module logger from the module that emitted the warning.

    ```python
    import warnings
    from rats.logs import showwarning

    warnings.showwarning = showwarning
    warnings.warn("This is a custom warning", UserWarning)
    ```

    Args:
        message: The warning message instance or string.
        category: The category of the warning (e.g., [DeprecationWarning][], [UserWarning][]).
        filename: The path to the file where the warning originated.
        lineno: The line number in the file where the warning originated.
        file: Ignored. Included for compatibility with the standard warnings.showwarning signature.
        line: The line of source code to be included in the warning message, if available.
    """
    if file is not None:
        raise ValueError(file)

    formatted_message = warnings.formatwarning(message, category, filename, lineno, line)

    try:
        for _module_name, module in sys.modules.items():
            module_path = getattr(module, "__file__", None)
            if module_path and Path(filename).is_file() and Path(module_path).samefile(filename):
                module_name = _module_name
                break
        else:
            # unsure what module to use, but we can default to "py.warnings" like the original handler
            module_name = "py.warnings"
    except Exception:
        # fall back to the default behavior and avoid ever failing from within logging functions
        module_name = "py.warnings"

    source_logger = logging.getLogger(module_name)
    source_logger.warning(formatted_message)
