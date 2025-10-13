"""
This component is intentionally left empty.

The rats component is meant to be used as a meta package to easily install other rats-* components.
No source or tests should be needed but we need this init file in order to have uv detect this
as a proper package that can be built into a wheel.

Using the rats package with [apps] and [devtools] extras allows us to define the dependency once
and ensure the same version is used across all rats packages installed.
"""
