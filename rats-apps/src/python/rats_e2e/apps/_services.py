from rats import apps


@apps.autoscope
class ExampleAppServices:
    INPUT = apps.ServiceId[str]("input")
