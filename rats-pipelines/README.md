# rats-pipelines

## Lorenzo's Random Dev Conventions Brain Dump

### Package Structure

- Everything goes into a top-level namespace package named `rats`.
- Do not nest public packages more than 1 level deep inside of `rats`.
- All python modules are private with underscore prefix.
- Define public APIs in `__init__.py` files using `__all__`.
- Use relative imports to import from adjacent python files.
- Never import from `.`.
- Excluding namespace packages, never import from parent packages.

### Tests

- Match the `src/python` directory structure.
- Each file in `src/python` has a matching `test_*.py` file.
- Every class in `src/python` has a matching `Test[class-name]` test class.
- Create a `TestFunctions` class for testing loose functions in a module.
- Avoid fixtures as much as possible.
- Mock/Fake any **Objects** other than the class being tested.
- Never require a network connection for running unit tests.
