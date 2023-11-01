import pytest

from oneml.habitats.pipeline_operations._datasets._utils import extend_uri_path, get_relative_path


@pytest.mark.parametrize(
    "url, relpath, expected",
    [
        ("http://example.com/path", "to/resource", "http://example.com/path/to/resource"),
        ("http://example.com/path/", "/to/resource", "http://example.com/path/to/resource"),
        ("http://example.com/path/", "", "http://example.com/path/"),
        ("http://example.com/path", "", "http://example.com/path"),
        ("memory:///path", "to/resource", "memory:///path/to/resource"),
        ("memory:///path/", "/to/resource", "memory:///path/to/resource"),
        ("file:///path", "to/resource", "file:///path/to/resource"),
        ("file:///path/", "/to/resource", "file:///path/to/resource"),
        (
            "abfss://jupyterscratch01@jupyterscratch01.dfs.core.windows.net/temp/path",
            "to/resource",
            "abfss://jupyterscratch01@jupyterscratch01.dfs.core.windows.net/temp/path/to/resource",
        ),
        (
            "abfss://jupyterscratch01@jupyterscratch01.dfs.core.windows.net/temp/path/",
            "/to/resource",
            "abfss://jupyterscratch01@jupyterscratch01.dfs.core.windows.net/temp/path/to/resource",
        ),
        (
            "ampds://repertoire.experiment-configs.cmv.CMVBaselineExperimentConfig.parquet/parquet/samples?namespace=production&partition=2023-08-20",
            "to/resource",
            "ampds://repertoire.experiment-configs.cmv.CMVBaselineExperimentConfig.parquet/parquet/samples/to/resource?namespace=production&partition=2023-08-20",
        ),
        (
            "ampds://repertoire.experiment-configs.cmv.CMVBaselineExperimentConfig.parquet/parquet/samples/?namespace=production&partition=2023-08-20",
            "/to/resource",
            "ampds://repertoire.experiment-configs.cmv.CMVBaselineExperimentConfig.parquet/parquet/samples/to/resource?namespace=production&partition=2023-08-20",
        ),
        (
            "ampds://repertoire.experiment-configs.cmv.CMVBaselineExperimentConfig.parquet?namespace=production&partition=2023-08-20",
            "to/resource",
            "ampds://repertoire.experiment-configs.cmv.CMVBaselineExperimentConfig.parquet/to/resource?namespace=production&partition=2023-08-20",
        ),
        (
            "ampds://repertoire.experiment-configs.cmv.CMVBaselineExperimentConfig.parquet/?namespace=production&partition=2023-08-20",
            "/to/resource",
            "ampds://repertoire.experiment-configs.cmv.CMVBaselineExperimentConfig.parquet/to/resource?namespace=production&partition=2023-08-20",
        ),
    ],
)
def test_extend_url_path(url: str, relpath: str, expected: str) -> None:
    result = extend_uri_path(url, relpath)
    assert result == expected


@pytest.mark.parametrize(
    "base_uri, target_uri, expected",
    [
        ("http://example.com/path/to", "http://example.com/path/to/resource", "resource"),
        (
            "file:///path/to",
            "file:///path/to/another/resource",
            "another/resource",
        ),
        (
            "ampds://DSname/path/to?partition=2020-10-11",
            "ampds://DSname/path/to/resource?partition=2020-10-11",
            "resource",
        ),
    ],
)
def test_get_relative_path(base_uri: str, target_uri: str, expected: str) -> None:
    result = get_relative_path(base_uri, target_uri)
    assert result == expected


@pytest.mark.parametrize(
    "base_uri, target_uri",
    [
        ("http://example.com/path/to", "http://example.com/path/from/resource"),
        ("http://example.com/path/to", "http://another.com/path/to/resource"),
        ("http://example.com/path/to", "abfss://example.com/path/to/resource"),
        (
            "ampds://DSname/path/to?partition=2020-10-11",
            "ampds://DSname/path/to/resource?partition=2020-10-10",
        ),
    ],
)
def test_get_relative_path_error(base_uri: str, target_uri: str) -> None:
    with pytest.raises(ValueError):
        get_relative_path(base_uri, target_uri)
