import pytest

from oneml.processors.identifiers import Identifier, ObjectIdentifier, SimpleObjectIdentifier

def test_identifier():
    s = Identifier("identifier/aa")
    assert isinstance(s, Identifier)
    assert isinstance(s, str)

def test_object_identifier():
    s = ObjectIdentifier("id/aa")
    assert isinstance(s, ObjectIdentifier)
    assert isinstance(s, Identifier)
    assert isinstance(s, str)
    with pytest.raises(ValueError):
        s = ObjectIdentifier("id.aa")

def test_simple_object_identifier():
    s = SimpleObjectIdentifier("id")
    assert isinstance(s, SimpleObjectIdentifier)
    assert isinstance(s, ObjectIdentifier)
    assert isinstance(s, Identifier)
    assert isinstance(s, str)
    with pytest.raises(ValueError):
        s = SimpleObjectIdentifier("id.aa")
    with pytest.raises(ValueError):
        s = SimpleObjectIdentifier("id/aa")
