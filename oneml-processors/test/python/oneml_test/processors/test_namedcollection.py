from oneml.processors.utils import namedcollection


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


def test_namedcollection_to_dict() -> None:
    t = {"foo": 1, "bar": 2, "hey": 3}
    n = namedcollection(t)
    assert n._asdict() == t


def test_namedcollection_repr() -> None:
    t = {"foo": 1, "bar": 2, "hey": 3}
    n = namedcollection(t)
    assert repr(n) == "namedcollection(foo=1, bar=2, hey=3)"


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


def test_nameset_or() -> None:
    n1 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
    n2 = namedcollection({"foo": 1, "bee": 2, "bur": 3})
    n3 = n1 | n2
    assert n3 == namedcollection({"foo": 1, "bar": 2, "hey": 3, "bee": 2, "bur": 3})


def test_recursive_nameset_or() -> None:
    n1 = namedcollection({"foo": 1, "bar": 2, "hey": namedcollection({"bla": 1, "blu": 2})})
    n2 = namedcollection(
        {"foo": 1, "bee": 2, "bur": 3, "hey": namedcollection({"blo": 3, "blu": 2})}
    )
    n3 = n1 | n2
    assert n3 == namedcollection(
        {
            "foo": 1,
            "bar": 2,
            "hey": namedcollection({"bla": 1, "blu": 2, "blo": 3}),
            "bee": 2,
            "bur": 3,
        }
    )


def test_recursive_nameset_sub() -> None:
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
