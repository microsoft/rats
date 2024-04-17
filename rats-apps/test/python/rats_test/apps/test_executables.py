from rats import apps


class TestExecutables:
    def test_basics(self) -> None:
        times = 0

        def run() -> None:
            nonlocal times
            times = times + 1

        app = apps.App(run)
        app.execute()

        assert times == 1

        for _ in range(4):
            app.execute()

        assert times == 5
