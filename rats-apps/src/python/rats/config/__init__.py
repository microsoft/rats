"""
Library for config <-> object transformations.

Concepts:

1. Factory: a callable service that creates an object from primitives or other objects.
2. Configuration: either one of:
   * a primitive.
   * a list of configurations.
   * a dictionary with str keys and configuration values with no __factory_id__ key.
   * a dictionary with str keys and configuration values with a __factory_id__ key.

"""
