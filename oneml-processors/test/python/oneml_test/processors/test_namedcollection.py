import pytest

from oneml.processors.utils import namedcollection


def test_namedcollection_init() -> None:
    n1 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
    assert n1.foo == 1 and n1.bar == 2 and n1.hey == 3

    n2 = namedcollection(foo=1, bar=2, hey=3)
    assert n2.foo == 1 and n2.bar == 2 and n2.hey == 3

    n3 = namedcollection((("foo", 1), ("bar", 2), ("hey", 3)))
    assert n3.foo == 1 and n3.bar == 2 and n3.hey == 3

    n4 = namedcollection([("foo", 1), ("bar", 2), ("hey", 3)], boo=4)
    assert n4.foo == 1 and n4.bar == 2 and n4.hey == 3 and n4.boo == 4

    n5 = namedcollection([("foo.foo", 1), ("foo.bar", 2), ("bar.bar", 2), ("hey", 3)], boo=4)
    assert n5.foo.foo == 1 and n5.foo.bar == 2 and n5.bar.bar == 2 and n5.hey == 3 and n5.boo == 4  # type: ignore[union-attr]

    n6 = namedcollection({"foo": 1, "bar": 2, "hey": n1}, boo=4)
    assert n6.foo == 1 and n6.bar == 2 and n6.hey == n1 and n6.boo == 4
    assert n6.hey.foo == 1 and n6.hey.bar == 2 and n6.hey.hey == 3  # type: ignore[attr-defined]

    n7 = namedcollection({"foo.foo": 1, "foo.bar": 2, "bar.bar": 2, "hey": 3}, boo=4)
    assert n7.foo.foo == 1 and n7.bar.bar == 2 and n7.hey == 3 and n7.boo == 4  # type: ignore[union-attr]

    n8 = namedcollection({"foo": n1, "foo.tee": 2})
    assert n8.foo.foo == 1 and n8.foo.bar == 2 and n8.foo.hey == 3 and n8.foo.tee == 2  # type: ignore[attr-defined]

    n9 = namedcollection({"foo.tee": 2, "foo": n1})
    assert n9.foo.foo == 1 and n9.foo.bar == 2 and n9.foo.hey == 3 and n9.foo.tee == 2  # type: ignore[attr-defined]


def test_namedcollection_eq() -> None:
    t = {"foo": 1, "bar": 2, "hey": 3}
    n1 = namedcollection(t)
    n2 = namedcollection(t)
    assert n1 == n2
    assert n1 == namedcollection({k: v for k, v in reversed(t.items())})


def test_namedcollection_len() -> None:
    n = namedcollection({"foo": 1, "bar": 2, "hey": 3})
    assert len(n) == 3


def test_namedcollection_iter() -> None:
    t = {"foo": 1, "bar": 2, "hey": 3}
    n = namedcollection(t)
    assert tuple(iter(n)) == tuple(iter(t))


def test_namedcollection_hash() -> None:
    t = {"foo": 1, "bar": 2, "hey": 3}
    n1 = namedcollection(t)
    n2 = namedcollection(t)
    assert hash(n1) == hash(n2)


def test_namedcollection_contains() -> None:
    t = {"foo": 1, "bar": 2, "hey": 3}
    n = namedcollection(t)
    assert "foo" in n
    assert "bar" in n
    assert "hey" in n
    assert "yee" not in n


def test_namecollection_getitem() -> None:
    n3 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
    n2 = namedcollection({"foo": 1, "bar": n3, "hey": 3})
    n1 = namedcollection({"foo": 1, "bee": n2, "bur": 3})

    assert n1["foo"] == 1
    assert n1["bee"] == n2
    assert n1["bee.foo"] == 1
    assert n1["bee.bar"] == n3
    assert n1["bee.hey"] == 3
    assert n1["bur"] == 3
    assert n1["bee.bar.foo"] == 1
    assert n1["bee.bar.bar"] == 2
    assert n1["bee.bar.hey"] == 3


def test_namedcollection_asdict() -> None:
    t = {"foo": 1, "bar": 2, "hey": 3}
    n3 = namedcollection(t)
    n2 = namedcollection({"foo": 1, "bar": n3, "hey": 3})
    n1 = namedcollection({"foo": 1, "bee": n2, "bur": 3})

    assert n3._asdict() == t

    assert n1._asdict() == {
        "foo": 1,
        "bee.foo": 1,
        "bee.bar.foo": 1,
        "bee.bar.bar": 2,
        "bee.bar.hey": 3,
        "bee.hey": 3,
        "bur": 3,
    }
    for k, v in n1._asdict().items():
        assert n1[k] == v

    assert namedcollection(n1._asdict()) == n1
    assert namedcollection(n2._asdict()) == n2
    assert namedcollection(n3._asdict()) == n3


def test_namedcollection_repr() -> None:
    n1 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
    assert repr(n1) == "namedcollection(foo=1, bar=2, hey=3)"

    n2 = namedcollection({"foo": 1, "bar": n1, "hey": 3})
    assert repr(n2) == "namedcollection(foo=1, bar.foo=1, bar.bar=2, bar.hey=3, hey=3)"


def test_namedcollection_replace() -> None:
    n1 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
    n2 = n1._replace(foo=4)
    assert n2 == namedcollection({"foo": 4, "bar": 2, "hey": 3})

    n3 = n1._replace({"foo": 4}, bar=5)
    assert n3 == namedcollection({"foo": 4, "bar": 5, "hey": 3})

    with pytest.raises(TypeError):
        n1._replace({"foo": 4}, {"bar": 5})  # type: ignore[call-arg]

    n4 = namedcollection({"foo": 1, "bar.bar": 2, "bar.foo": 4, "hey": 3})
    n5 = n4._replace({"bar.foo": 5, "bar.bar": 6})
    assert n5 == namedcollection({"foo": 1, "bar.bar": 6, "bar.foo": 5, "hey": 3})

    n6 = n4._replace({"bar.bee": 5})  # add new value
    assert n6 == namedcollection({"foo": 1, "bar.bar": 2, "bar.foo": 4, "bar.bee": 5, "hey": 3})


def test_namedcollection_union() -> None:
    t1 = {"foo": 1, "bar": 2, "hey": 3}
    t2 = {"foo": 1, "bee": 2, "bur": 3}
    t3 = {"bla": 1, "blu": 2}

    n1 = namedcollection(t1)
    n2 = namedcollection(t2)
    n3 = namedcollection(t3)

    n4 = n1._union(n2, n3)
    assert n4 == namedcollection(
        {"foo": 1, "bar": 2, "hey": 3, "bee": 2, "bur": 3, "bla": 1, "blu": 2}
    )


def test_namedcollection_or() -> None:
    n1 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
    n2 = namedcollection({"foo": 1, "bee": 2, "bur": 3})
    n3 = n1 | n2
    assert n3 == namedcollection({"foo": 1, "bar": 2, "hey": 3, "bee": 2, "bur": 3})


def test_recursive_namedcollection_or() -> None:
    n1 = namedcollection({"foo": 1, "bar": 2, "hey": namedcollection({"bla": 1, "blu": 2})})
    n2 = namedcollection(
        {"foo": 1, "bee": 2, "bur": 3, "hey": namedcollection({"blo": 3, "blu": 2})}
    )
    n3 = n1 | n2
    n4 = namedcollection(
        {"foo": 1, "bar": 2, "hey.bla": 1, "hey.blu": 2, "hey.blo": 3, "bee": 2, "bur": 3}
    )
    assert n3 == n4

    n5 = n3 | {"foo": 1, "bee": 2, "bur": 3, "hey.blo": 3, "hey.blu": 2}
    assert n5 == n4


def test_namedcollection_sub() -> None:
    n1 = namedcollection({"foo": 1, "boo": 2, "bar": 3, "hey": 4})
    n2 = namedcollection({"foo": 1, "bee": 2, "bur": 3, "hey": 4})
    n3 = namedcollection({"foo": 1, "boo": 2, "bar": n2, "hey": 4, "bee": 2, "bur": 3})

    n4 = n1 - n2
    assert n4 == namedcollection({"boo": 2, "bar": 3})

    n5 = n2 - n1
    assert n5 == namedcollection({"bee": 2, "bur": 3})

    n6 = n1 - ("foo", "boo")
    assert n6 == namedcollection({"bar": 3, "hey": 4})

    n7 = n1 - ("foo", "boo", "bar", "hey")
    assert n7 == namedcollection()

    n8 = n3 - ("bar",)
    assert n8 == namedcollection({"foo": 1, "boo": 2, "hey": 4, "bee": 2, "bur": 3})

    n9 = n3 - ("bar.bur",)
    assert n9 == namedcollection(
        {"foo": 1, "boo": 2, "bar": n2 - ("bur",), "hey": 4, "bee": 2, "bur": 3}
    )

    n10 = n3 - ("bar.foo", "bar.bee", "bar.bur", "bar.hey")
    assert n10 == namedcollection({"foo": 1, "boo": 2, "hey": 4, "bee": 2, "bur": 3})


def test_namedcollection_rename() -> None:
    n1 = namedcollection({"foo": 1, "boo": 2, "bar": 3, "hey": 4})
    n12 = n1._rename({"foo": "foo2", "boo": "boo2"})
    assert n12 == namedcollection({"foo2": 1, "boo2": 2, "bar": 3, "hey": 4})

    n2 = namedcollection({"foo": 1, "bee": 2, "bur": 3, "hey": 4})
    n3 = namedcollection({"foo": 1, "boo": 2, "bar": n2, "hey": 4, "bee": 2, "bur": 3})
    n4 = n3._rename({"bar": "bar2"})
    assert n4 == namedcollection({"foo": 1, "boo": 2, "bar2": n2, "hey": 4, "bee": 2, "bur": 3})

    n5 = n3._rename({"bar": "bar2", "bar2.bee": "bar2.bee2"})
    assert n5 == namedcollection(
        {"foo": 1, "boo": 2, "bar2": n2._rename({"bee": "bee2"}), "hey": 4, "bee": 2, "bur": 3}
    )

    n6 = n3._rename({"bar": "bar2", "bar2.bee": "bar2.bee2", "bar2.bee2": "bar2.bee3"})
    assert n6 == namedcollection(
        {"foo": 1, "boo": 2, "bar2": n2._rename({"bee": "bee3"}), "hey": 4, "bee": 2, "bur": 3}
    )

    n7 = n3._rename({"bar.bee": "bar2.bee2"})
    assert n7 == namedcollection(
        {
            "foo": 1,
            "boo": 2,
            "bar": n2 - ("bee",),
            "hey": 4,
            "bee": 2,
            "bur": 3,
            "bar2": n2._rename({"bee": "bee2"}) - ("foo", "bur", "hey"),
        }
    )

    n8 = n3._rename(
        {
            "bar.foo": "bar2.foo",
            "bar.bee": "bar2.bee",
            "bar.bur": "bar2.bur",
            "bar.hey": "bar2.hey",
        }
    )
    assert n8 == namedcollection({"foo": 1, "boo": 2, "bar2": n2, "hey": 4, "bee": 2, "bur": 3})


def test_namedcollection_find() -> None:
    n1 = namedcollection({"foo": 1, "boo": 2, "bar": 3, "hey": 3})
    n2 = namedcollection({"foo": 1, "bee": 2, "bur": 3, "hey": 4})
    n3 = namedcollection({"foo": 1, "boo": 2, "bar": n2, "hey": 4, "bee": 2, "bur": 3})
    n4 = namedcollection({"foo": 1, "boo": 2, "bar": (5,), "hey": 4, "bee": 2, "bur": 3})

    assert n1._find(1) == ("foo",)
    assert n1._find(2) == ("boo",)
    assert n1._find(3) == ("bar", "hey")
    assert n1._find(4) == ()
    assert n3._find(2) == ("boo", "bar.bee", "bee")

    assert n1._find(1, 2) == ("foo", "boo")
    assert n1._find(1, 3) == ("foo", "bar", "hey")

    assert n3._find(1, 2) == ("foo", "bar.foo", "boo", "bar.bee", "bee")
    assert n4._find(5) == ("bar",)


def test_namedcollection_depth() -> None:
    n1 = namedcollection({"foo": 1, "boo": 2, "bar": 3, "hey": 3})
    assert n1._depth == 0

    n2 = namedcollection({"foo.foo": 1, "foo.bar": 2, "bar.bar": 2, "hey": 3}, boo=4)
    assert n2._depth == 1

    n3 = namedcollection({"foo.foo.foo": 1, "foo.bar": 2, "bar.bar": 2, "hey": 3}, boo=4)
    assert n3._depth == 2
