from collections.abc import Mapping
from typing import Any, NamedTuple

from furl import furl

from rats.processors._legacy_subpackages.dag import IProcess
from rats.processors._legacy_subpackages.io import Manifest


class BuildManifestProcessorOutput(NamedTuple):
    manifest: Manifest


class BuildManifestProcessor(IProcess):
    def _get_relative_path(self, base_uri: str, target_uri: str) -> str:
        """Return the relative path of target_uri from base_uri, or target_uri if no relative path can be calculated."""
        base_parts = furl(base_uri)
        target_parts = furl(target_uri)

        base_path_segments = list[str](filter(None, base_parts.path.segments))
        target_path_segments = list[str](filter(None, target_parts.path.segments))

        base_parts = base_parts.copy().remove(path=True)
        target_parts = target_parts.copy().remove(path=True)

        # Check if the base and target URIs are identical up to the path component
        if base_parts != target_parts:
            return target_uri

        if base_path_segments != target_path_segments[: len(base_path_segments)]:
            return target_uri

        return "/".join(target_path_segments[len(base_path_segments) :])

    def process(self, **kwds: Any) -> BuildManifestProcessorOutput:
        """Build a manifest of relative paths from a base uri and a set of named output uris.

        Args:
            output_base_uri (str): The base uri to use for the manifest.
            _NAME: The output uris to include in the manifest, where NAME is the name of the,
                output, which will become the key in the manifest's relative paths dictionary.
        """
        output_base_uri = kwds["output_base_uri"]
        output_uris: Mapping[str, str] = {k[1:]: v for k, v in kwds.items() if k.startswith("_")}
        unexpected_arguments = {
            k for k in kwds if k != "output_base_uri" and not k.startswith("_")
        }
        if unexpected_arguments:
            raise ValueError(f"Unexpected arguments: {unexpected_arguments}")
        uris = {
            name: self._get_relative_path(output_base_uri, uri)
            for name, uri in output_uris.items()
        }
        manifest = Manifest(entry_uris=uris)
        return BuildManifestProcessorOutput(manifest=manifest)
