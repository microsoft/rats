import sys
from pathlib import Path

import pytest


def run() -> None:
    files_to_test = [sys.argv[1]]
    if files_to_test[0].startswith("src/python/immunopipeline/"):
        test_path = Path(
            files_to_test[0].replace("src/python/immunopipeline/", "test/python/immunopipeline_test/"),
        )
        test_package = str(test_path.parent)
        files_to_test.append(str(test_package))

    print(f"running tests for files: {files_to_test}")

    sys.exit(pytest.main([
        "--no-cov",
        "--noconftest",
        "--capture", "tee-sys",
        *files_to_test,
    ]))
