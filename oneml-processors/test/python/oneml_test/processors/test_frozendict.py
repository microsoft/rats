from oneml.processors.utils import frozendict


def test_frozendict() -> None:
    d1 = dict(boo="foo")
    fd: frozendict[str, str] = frozendict(d1)
    d2 = dict(fd)
    assert d1 == d2
