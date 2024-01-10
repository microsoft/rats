import os.path
from urllib.parse import urlparse, urlunparse


def extend_uri_path(uri: str, relpath: str) -> str:
    if not relpath:
        return uri
    parsed_uri = urlparse(uri)
    current_path = parsed_uri.path
    if not current_path.startswith("/"):
        current_path = "/" + current_path
    relpath = relpath.lstrip("/")
    new_path = os.path.join(parsed_uri.path, relpath)
    if not parsed_uri.netloc:
        new_path = "//" + new_path
    extended_uri = urlunparse(
        (
            parsed_uri.scheme,
            parsed_uri.netloc,
            new_path,
            parsed_uri.params,
            parsed_uri.query,
            parsed_uri.fragment,
        )
    )
    return extended_uri


def get_relative_path(base_uri: str, target_uri: str) -> str:
    """Return the relative path of target_uri from base_uri."""
    parsed_base_uri = urlparse(base_uri)
    parsed_target_uri = urlparse(target_uri)

    base_path = parsed_base_uri.path
    if not base_path.startswith("/"):
        base_path = "/" + base_path

    target_path = parsed_target_uri.path
    if not target_path.startswith("/"):
        target_path = "/" + target_path

    parsed_base_uri_without_path = parsed_base_uri._replace(path="")
    parsed_target_uri_without_path = parsed_target_uri._replace(path="")

    # Check if the base and target URIs are identical up to the path component
    if parsed_base_uri_without_path != parsed_target_uri_without_path:
        raise ValueError(f"target URI {target_uri} is not a child of base URI {base_uri}")
    if os.path.commonpath([base_path, target_path]) != os.path.commonpath([base_path]):
        raise ValueError(f"target URI {target_uri} is not a child of base URI {base_uri}")

    return os.path.relpath(target_path, base_path)
