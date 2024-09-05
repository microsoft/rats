from rats import apps, config
from rats.config import Services as ConfigServices
from collections.abc import Sequence, Mapping
from typing import cast, Any


class A:
    def __eq__(self, obj: Any) -> bool:
        return isinstance(obj, A)


class B:
    def __init__(self, num: int, s: str):
        self.num = num
        self.s = s

    def __eq__(self, obj: Any) -> bool:
        return isinstance(obj, B) and self.num == obj.num and self.s == obj.s


class C:
    def __init__(self, li: Sequence[int], a: A, db: Mapping[int, B]):
        self.li = li
        self.a = a
        self.db = db

    def __eq__(self, obj: Any) -> bool:
        return isinstance(obj, C) and self.li == obj.li and self.a == obj.a and self.db == obj.db


def _li(start: int, end: int, step: int) -> Sequence[int]:
    return tuple(range(start, end, step))


class Container(config.ConfigFactoryContainer):
    def __init__(self, app: apps.Container) -> None:
        super().__init__(app)

    @config.autoid_config_factory_service
    def a(self) -> A:
        return A()

    @config.autoid_config_factory_service
    def b(self, num: int, s: str) -> B:
        return B(num, s)

    @apps.autoid_factory_service
    def li(self, start: int, end: int, step: int) -> Sequence[int]:
        return tuple(range(start, end, step))

    @apps.autoid_factory_service
    def db(self) -> Mapping[int, B]:
        b_factory = self.get(apps.autoid(self.b))
        db = {
            0: b_factory(num=0, s="zero"),
            1: b_factory(num=1, s="one"),
        }
        return db

    @config.autoid_config_factory_service
    def c(self, li: Sequence[int], a: A, db: Mapping[int, B]) -> C:
        return C(li, a, db)


class App(apps.Container):
    @apps.container()
    def config_container(self) -> apps.Container:
        return config.PluginContainer(self)

    @apps.container()
    def container(self) -> apps.Container:
        return Container(self)


class Services:
    A = apps.autoid(Container.a)
    B = apps.autoid(Container.b)
    LI = apps.autoid(Container.li)
    DB = apps.autoid(Container.db)
    C = apps.autoid(Container.c)


class TestConfig:
    _app: App = App()

    def get_a(self) -> A:
        factory = self._app.get(Services.A)
        a = factory()
        return a

    def get_a_config(self) -> config.Configuration:
        a = self.get_a()
        config_getter = self._app.get(ConfigServices.GET_CONFIGURATION_FROM_OBJECT)
        config = config_getter(a)
        return config

    def test_a_config(self) -> None:
        a_config = self.get_a_config()
        expected = config.FactoryConfiguration(
            _factory_service_id_=Services.A.name,
        )
        assert a_config == expected

    def test_a_reconstructed(self) -> None:
        a_config = self.get_a_config()
        config_to_object = self._app.get(ConfigServices.CONFIGURATION_TO_OBJECT)
        a = config_to_object(a_config)
        assert isinstance(a, A)

    def get_b(self) -> B:
        factory = self._app.get(Services.B)
        b = factory(num=1, s="one")
        return b

    def get_b_config(self) -> config.Configuration:
        b = self.get_b()
        config_getter = self._app.get(ConfigServices.GET_CONFIGURATION_FROM_OBJECT)
        config = config_getter(b)
        return config

    def test_b_config(self) -> None:
        b_config = self.get_b_config()
        expected = config.FactoryConfiguration(
            _factory_service_id_=Services.B.name,
            _kwargs_=dict(num=1, s="one"),
        )
        assert b_config == expected

    def test_b_reconstructed(self) -> None:
        b_config = self.get_b_config()
        config_to_object = self._app.get(ConfigServices.CONFIGURATION_TO_OBJECT)
        b = config_to_object(b_config)
        assert isinstance(b, B)
        assert b.num == 1
        assert b.s == "one"

    def test_alt_b_reconstructed(self) -> None:
        b_config = config.FactoryConfiguration(
            _factory_service_id_=Services.B.name,
            _kwargs_={"num": 2, "s": "two"},
        )
        config_to_object = self._app.get(ConfigServices.CONFIGURATION_TO_OBJECT)
        b = config_to_object(b_config)
        assert isinstance(b, B)
        assert b.num == 2
        assert b.s == "two"

    def get_li(self) -> Sequence[int]:
        factory = self._app.get(Services.LI)
        li = factory(start=4, end=10, step=2)
        return li

    def get_li_config(self) -> config.Configuration:
        li = self.get_li()
        config_getter = self._app.get(ConfigServices.GET_CONFIGURATION_FROM_OBJECT)
        config = config_getter(li)
        return config

    def test_li_config(self) -> None:
        li_config = self.get_li_config()
        expected = (4, 6, 8)
        assert li_config == expected

    def test_li_reconstructed(self) -> None:
        li_config = self.get_li_config()
        config_to_object = self._app.get(ConfigServices.CONFIGURATION_TO_OBJECT)
        li = config_to_object(li_config)
        assert isinstance(li, tuple)
        assert li == (4, 6, 8)

    def get_db(self) -> Mapping[int, B]:
        return self._app.get(Services.DB)()

    def get_db_config(self) -> config.Configuration:
        db = self.get_db()
        config_getter = self._app.get(ConfigServices.GET_CONFIGURATION_FROM_OBJECT)
        config = config_getter(db)
        return config

    def test_db_config(self) -> None:
        db_config = self.get_db_config()
        expected = {
            0: config.FactoryConfiguration(
                _factory_service_id_=Services.B.name,
                _kwargs_=dict(num=0, s="zero"),
            ),
            1: config.FactoryConfiguration(
                _factory_service_id_=Services.B.name,
                _kwargs_=dict(num=1, s="one"),
            ),
        }
        assert db_config == expected

    def test_db_reconstructed(self) -> None:
        db_config = self.get_db_config()
        config_to_object = self._app.get(ConfigServices.CONFIGURATION_TO_OBJECT)
        db = cast(Mapping[int, B], config_to_object(db_config))
        assert isinstance(db, dict)
        assert len(db) == 2
        assert 0 in db
        assert 1 in db
        b0 = db[0]
        b1 = db[1]
        assert isinstance(b0, B)
        assert isinstance(b1, B)
        assert b0.num == 0
        assert b0.s == "zero"
        assert b1.num == 1
        assert b1.s == "one"

    def get_c(self) -> C:
        return self._app.get(Services.C)(self.get_li(), self.get_a(), self.get_db())

    def get_c_config(self) -> config.Configuration:
        c = self.get_c()
        config_getter = self._app.get(ConfigServices.GET_CONFIGURATION_FROM_OBJECT)
        config = config_getter(c)
        return config

    def test_c_config(self) -> None:
        c_config = self.get_c_config()
        expected = config.FactoryConfiguration(
            _factory_service_id_=Services.C.name,
            _args_=(self.get_li_config(), self.get_a_config(), self.get_db_config()),
        )
        assert c_config == expected

    def test_config_to_config(self) -> None:
        c_config = self.get_c_config()
        object_to_config = self._app.get(ConfigServices.GET_CONFIGURATION_FROM_OBJECT)
        c_config2 = object_to_config(c_config)
        assert c_config2 == c_config

    def test_c_reconstructed(self) -> None:
        c_config = self.get_c_config()
        config_to_object = self._app.get(ConfigServices.CONFIGURATION_TO_OBJECT)
        c = config_to_object(c_config)
        assert isinstance(c, C)
        assert c.li == (4, 6, 8)
        assert isinstance(c.a, A)
        assert len(c.db) == 2
        assert 0 in c.db
        assert 1 in c.db
        b0 = c.db[0]
        b1 = c.db[1]
        assert isinstance(b0, B)
        assert isinstance(b1, B)
        assert b0.num == 0
        assert b0.s == "zero"
        assert b1.num == 1
        assert b1.s == "one"

    def test_c_yaml(self) -> None:
        to_yaml = self._app.get(ConfigServices.TO_CONFIG_YAML)
        from_yaml = self._app.get(ConfigServices.FROM_CONFIG_YAML)

        c = self.get_c()
        yaml_str = to_yaml.to_str(c)
        c2 = from_yaml.get_object(yaml_str)
        assert c2 == c
