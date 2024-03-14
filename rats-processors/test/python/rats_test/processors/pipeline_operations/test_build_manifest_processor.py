from rats.processors.pipeline_operations._build_manifest_processor import (
    BuildManifestProcessor,
    Manifest,
)


def test_build_manifest_processor_empty_manifest() -> None:
    processor = BuildManifestProcessor()

    output = processor.process(output_base_uri="http://example.com")
    assert output.manifest == Manifest(entry_uris={})


def test_build_manifest_processor_base_uri_with_no_path() -> None:
    processor = BuildManifestProcessor()

    output = processor.process(
        output_base_uri="http://example.com",
        _output1="http://example.com/foo",
        _output2="http://different-example.com/bar",
    )
    assert output.manifest == Manifest(
        entry_uris={"output1": "foo", "output2": "http://different-example.com/bar"}
    )


def test_build_manifest_processor_base_uri_with_path() -> None:
    processor = BuildManifestProcessor()

    output = processor.process(
        output_base_uri="http://example.com/base/path/",
        _output1="http://example.com/base/path/to/output1",
        _output2="http://different-example.com/base/path/to/output2",
        _output3="http://example.com/base/other/path/to/output3",
    )
    assert output.manifest == Manifest(
        entry_uris={
            "output1": "to/output1",
            "output2": "http://different-example.com/base/path/to/output2",
            "output3": "http://example.com/base/other/path/to/output3",
        }
    )


def test_build_manifest_processor_unexpected_arguments() -> None:
    processor = BuildManifestProcessor()

    try:
        processor.process(
            output_base_uri="http://example.com",
            _output1="http://example.com/foo",
            unexpected_arg="baz",
        )
        raise AssertionError("Expected ValueError")
    except ValueError as e:
        assert str(e) == "Unexpected arguments: {'unexpected_arg'}"
