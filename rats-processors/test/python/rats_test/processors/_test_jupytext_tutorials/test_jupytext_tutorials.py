# Run the jupytext tutorials under rats-processors/docs/_jupytext_tutorials.
import contextlib
import importlib.util
from pathlib import Path

import pytest

# Get a list of all .py files in the directory
tutorial_path = (Path(__file__) / "../../_jupytext_tutorials/").resolve()
tutorial_files = tuple(tutorial_path.glob("*.py"))


# Generate a test for each file
@pytest.mark.skip_in_ci
@pytest.mark.parametrize("tutorial_file", tutorial_files)
def test_tutorial(tutorial_file: Path):
    # Import the tutorial file as a module
    spec = importlib.util.spec_from_file_location(tutorial_file.stem, tutorial_file)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(None):
        spec.loader.exec_module(module)
