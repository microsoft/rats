from oneml.processors.utils import orderedset


def test_orderedset_eq() -> None:
    t = ("foo", "boo", "bar", "hey", "boo")
    o1 = orderedset(t)
    o2 = orderedset(t)
    assert o1 == o2


def test_orderedset_len() -> None:
    o = orderedset(("foo", "boo", "bar", "hey", "boo"))
    assert len(o) == 4


def test_orderedset_iter() -> None:
    t = ("foo", "boo", "bar", "hey", "boo")
    o = orderedset(t)
    assert tuple(iter(o)) == tuple(iter(t[:-1]))


def test_orderedset_hash() -> None:
    t = ("foo", "boo", "bar", "hey", "boo")
    o1 = orderedset(t)
    o2 = orderedset(t)
    assert hash(o1) == hash(o2)


def test_orderedset_contains() -> None:
    t = ("foo", "boo", "bar", "hey", "boo")
    o = orderedset(t)
    assert "foo" in o
    assert "boo" in o
    assert "bar" in o
    assert "hey" in o
    assert "yee" not in o


def test_orderedset_order() -> None:
    t1 = ("foo", "boo", "bar", "hey")
    t2 = ("foo", "boo", "bar", "hey", "boo")
    o1 = orderedset(t1)
    o2 = orderedset(t2)
    assert tuple(o1) == t1
    assert tuple(o2) == t2[:-1]


def test_orderedset_repr() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey"))
    assert repr(o1) == "orderedset('foo', 'boo', 'bar', 'hey')"


def test_orderedset_union() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey", "foo"))
    o2 = orderedset(("foo", "bee", "bur", "hey"))
    o3 = orderedset(("bla", "blu"))
    o4 = o1.union(o2, o3)
    assert o4 == orderedset(("foo", "boo", "bar", "hey", "bee", "bur", "bla", "blu"))


def test_orderedset_or() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey", "foo"))
    o2 = orderedset(("foo", "bee", "bur", "hey"))
    o3 = o1 | o2
    assert o3 == orderedset(("foo", "boo", "bar", "hey", "bee", "bur"))


def test_orderedset_intersection() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey", "foo"))
    o2 = orderedset(("foo", "bee", "bur", "hey"))
    o3 = orderedset(("foo", "hey", "bla", "blu"))
    o4 = o1.intersection(o2, o3)
    assert o4 == orderedset(("foo", "hey"))


def test_orderedset_and() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey"))
    o2 = orderedset(("foo", "bee", "bur", "hey"))
    o3 = o1 & o2
    assert o3 == orderedset(("foo", "hey"))


def test_orderedset_sub() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey"))
    o2 = orderedset(("foo", "bee", "bur", "hey"))
    o3 = o1 - o2
    assert o3 == orderedset(("boo", "bar"))


def test_orderedset_index() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey"))
    assert o1[0] == "foo"
    assert o1[1] == "boo"
    assert o1[2] == "bar"
    assert o1[3] == "hey"


def test_orderedset_slice() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey"))
    assert o1[0:1] == o1[-4:-3] == orderedset(("foo",))
    assert o1[1:2] == o1[-3:-2] == orderedset(("boo",))
    assert o1[2:3] == o1[-2:-1] == orderedset(("bar",))
    assert o1[3:4] == o1[-1:] == orderedset(("hey",))
    assert o1[0:2] == o1[-4:-2] == orderedset(("foo", "boo"))
    assert o1[1:3] == o1[-3:-1] == orderedset(("boo", "bar"))
    assert o1[2:4] == o1[-2:] == orderedset(("bar", "hey"))
    assert o1[0:3] == o1[-4:-1] == orderedset(("foo", "boo", "bar"))
    assert o1[1:4] == o1[-3:] == orderedset(("boo", "bar", "hey"))
    assert o1[0:4] == o1[-4:] == orderedset(("foo", "boo", "bar", "hey"))


def test_orderedset_reversed() -> None:
    o1 = orderedset(("foo", "boo", "bar", "hey"))
    assert orderedset(reversed(o1)) == orderedset(("hey", "bar", "boo", "foo"))
    assert o1 == orderedset(reversed(orderedset(reversed(o1))))
