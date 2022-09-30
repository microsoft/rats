# flake8: noqa
from __future__ import annotations

from dataclasses import dataclass

import pytest

from oneml.processors.sandbox.processors.assignable import Assignable


@dataclass
class _TestAssignable1(Assignable):
    a: int = 10
    b: str = "a"


@dataclass
class _TestAssignable2(Assignable):
    a: int = 10
    b: int = 100
    c: _TestAssignable1 = _TestAssignable1(a=30)
    d: _TestAssignable1 = _TestAssignable1(a=20)


def test_assign_to_simple_attribute():
    a = _TestAssignable1()
    b = a.assign(a=100)
    assert a.a == 10
    assert b.a == 100
    assert a.b == "a"
    assert b.b == "a"


def test_assign_to_nested_attribute():
    a = _TestAssignable2()
    b = a.assign(**{"b": 50, "d.b": "quack"})
    assert a.a == 10
    assert a.b == 100
    assert a.c.a == 30
    assert a.c.b == "a"
    assert a.d.a == 20
    assert a.d.b == "a"
    assert b.a == 10
    assert b.b == 50
    assert b.c is a.c
    assert b.d.a == 20
    assert b.d.b == "quack"


def test_assign_to_non_existing_attribute():
    a = _TestAssignable1()
    with pytest.raises(AttributeError):
        b = a.assign(c=1)


def test_assign_member_and_its_attribute():
    a = _TestAssignable2()
    b = a.assign(
        **{
            "c": _TestAssignable1(a=40, b="quack"),
            "c.a": 100,
        }
    )
    assert a.a == 10
    assert a.b == 100
    assert a.c.a == 30
    assert a.c.b == "a"
    assert a.d.a == 20
    assert a.d.b == "a"
    assert b.a is a.a
    assert b.b is a.b
    assert b.c.a == 100
    assert b.c.b == "quack"
    assert b.d is a.d
