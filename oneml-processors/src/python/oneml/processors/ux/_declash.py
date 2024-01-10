from collections.abc import Sequence

from ._pipeline import UPipeline


def find_non_clashing_name(name: str, existing_names: set[str]) -> str:
    suggest_name = name
    i = 0
    while suggest_name in existing_names:
        suggest_name = f"{name}_{i}"
        i += 1
    return suggest_name


def ensure_non_clashing_pipeline_names(*pipelines: UPipeline) -> Sequence[UPipeline]:
    """Given a list of pipelines return copies of them potentially renamed to avoid name clashes.

    Usage:
        pl1, pl2, pl3, pl4 = ensure_non_clashing_pipeline_names(pl1, pl2, pl3, pl4)

    Examples:
        If the names of [pl1, pl2, pl3] are "Loki", "Freyja", "Heimdall" and "Idunn" respectively,
        then the will be returned without changes.

        If the names of [pl1, pl2, pl3] are "Loki", "Loki", "Loki", "Loki" respectively, then the
        will pipelines will be renamed to "Loki", "Loki_0", "Loki_1", "Loki_2".

        If the names of [pl1, pl2, pl3] are "Loki", "Freyja", "Loki", "Freyja" respectively, then
        the will pipelines will be renamed to "Loki", "Freyja", "Loki_0", "Freyja_0".

        If the names of [pl1, pl2, pl3] are "Loki", "Freyja", "Loki", "Loki" respectively, then
        the will pipelines will be renamed to "Loki", "Freyja", "Loki_0", "Loki_1".
    """
    r_pipelines: list[UPipeline] = list(pipelines)
    for i, p in enumerate(r_pipelines):
        name = find_non_clashing_name(p.name, set([p.name for p in r_pipelines[:i]]))
        if name != p.name:
            r_pipelines[i] = p.decorate(name)
    return r_pipelines
