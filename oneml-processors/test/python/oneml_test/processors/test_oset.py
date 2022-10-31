from oneml.processors._orderedset import oset


def test_oset_eq() -> None:
    t = ("foo", "boo", "bar", "hey", "boo")
    o1 = oset(t)
    o2 = oset(t)
    assert o1 == o2


def test_oset_len() -> None:
    o = oset(("foo", "boo", "bar", "hey", "boo"))
    assert len(o) == 4


def test_oset_iter() -> None:
    t = ("foo", "boo", "bar", "hey", "boo")
    o = oset(t)
    assert tuple(iter(o)) == tuple(iter(t[:-1]))


def test_oset_hash() -> None:
    t = ("foo", "boo", "bar", "hey", "boo")
    o1 = oset(t)
    o2 = oset(t)
    assert hash(o1) == hash(o2)


def test_oset_contains() -> None:
    t = ("foo", "boo", "bar", "hey", "boo")
    o = oset(t)
    assert "foo" in o
    assert "boo" in o
    assert "bar" in o
    assert "hey" in o
    assert "yee" not in o


def test_oset_order() -> None:
    t1 = ("foo", "boo", "bar", "hey")
    t2 = ("foo", "boo", "bar", "hey", "boo")
    o1 = oset(t1)
    o2 = oset(t2)
    assert tuple(o1) == t1
    assert tuple(o2) == t2[:-1]


def test_oset_repr() -> None:
    o1 = oset(("foo", "boo", "bar", "hey"))
    assert repr(o1) == "orderedset('foo', 'boo', 'bar', 'hey')"


def test_oset_union() -> None:
    o1 = oset(("foo", "boo", "bar", "hey", "foo"))
    o2 = oset(("foo", "bee", "bur", "hey"))
    o3 = oset(("bla", "blu"))
    o4 = o1.union(o2, o3)
    assert o4 == oset(("foo", "boo", "bar", "hey", "bee", "bur", "bla", "blu"))


def test_oset_or() -> None:
    o1 = oset(("foo", "boo", "bar", "hey", "foo"))
    o2 = oset(("foo", "bee", "bur", "hey"))
    o3 = o1 | o2
    assert o3 == oset(("foo", "boo", "bar", "hey", "bee", "bur"))


def test_oset_intersection() -> None:
    o1 = oset(("foo", "boo", "bar", "hey", "foo"))
    o2 = oset(("foo", "bee", "bur", "hey"))
    o3 = oset(("foo", "hey", "bla", "blu"))
    o4 = o1.intersection(o2, o3)
    assert o4 == oset(("foo", "hey"))


def test_oset_and() -> None:
    o1 = oset(("foo", "boo", "bar", "hey"))
    o2 = oset(("foo", "bee", "bur", "hey"))
    o3 = o1 & o2
    assert o3 == oset(("foo", "hey"))


def test_oset_sub() -> None:
    o1 = oset(("foo", "boo", "bar", "hey"))
    o2 = oset(("foo", "bee", "bur", "hey"))
    o3 = o1 - o2
    assert o3 == oset(("boo", "bar"))
