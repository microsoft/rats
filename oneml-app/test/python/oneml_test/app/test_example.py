from oneml.app import ExampleObjects


class TestExampleObjects:
    def test_basics(self) -> None:
        client = ExampleObjects()
        assert client.get_thing() == 5
