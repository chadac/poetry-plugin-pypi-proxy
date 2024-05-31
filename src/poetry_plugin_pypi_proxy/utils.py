from __future__ import annotations

import hashlib
import importlib.metadata
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from poetry.utils.password_manager import HTTPAuthCredential

# try:
#     import pkg_resources
#     POETRY_VERSION = tuple(
#         map(int, pkg_resources.get_distribution("poetry").version.split(".")[:3])
#     )
# except ImportError:
POETRY_VERSION = tuple(map(int, importlib.metadata.version("poetry").split(".")[:3]))


if POETRY_VERSION <= (1, 2, 1):
    from poetry.core.semver.version import Version  # type: ignore
else:
    from poetry.core.constraints.version import Version  # type: ignore


# stop pycln from removing the above import
Version = Version


@dataclass
class PoetryAuthConfig:
    """
    This class is used for being able to represent what is needed for
    the source for Poetry
    """

    url: str
    http_auth: HTTPAuthCredential | None


def get_repo_id(repo_url: str) -> str:
    """
    Generate a unique identifier for the proxy server.

    Note that this can change between clones of this project.  This
    is used silently when caching packages and for the publisher, so
    it should have no effect on your build processes.

    :param repo_url: The proxy repo url

    :return repo id: A Unique Identifier for the proxy repo, this uses md5 hashing.
    """
    key = hashlib.md5((repo_url).encode()).hexdigest()
    return f"pypi-proxy-{key}"


def parse_url(url: str) -> str:
    """
    Remove suffix from url appropriately so it can be used by the proxy object.

    :param url: A URL string for parsing

    :return new_url: Returns the URL with simple suffix removed for using
    in the proxy object

    """
    return re.sub("/?(simple/?)?$", "", url)


def generate_poetry_auth_config(url: str) -> PoetryAuthConfig:
    """
    We need to account for a url with auth data to pass into Poetry with
    the proxy URL

    :param url: The URL string that we get from the env var

    :raises ValueError: This error gets raised when we receive a
    password without a username in the URL as this should not be possible.

    :return PoetrySourceConfig: Returns a TypedDict that contains username,
    password and a cleaned url

    """
    url_parts = urlparse(url)
    if url_parts.scheme == "" or url_parts.hostname is None:
        raise ValueError("Malformed URL either the scheme or hostname is missing")
    port = ""
    if url_parts.port is not None:
        port = f":{url_parts.port}"
    cleaned_url = f"{url_parts.scheme}://{url_parts.hostname}{port}{url_parts.path}"
    parsed_and_cleaned = parse_url(cleaned_url)
    if url_parts.username is not None and url_parts.password is not None:
        return PoetryAuthConfig(
            url=parsed_and_cleaned,
            http_auth=HTTPAuthCredential(url_parts.username, url_parts.password),
        )
    elif url_parts.username is not None and (
        url_parts.password == "" or url_parts.password is None
    ):
        return PoetryAuthConfig(
            url=parsed_and_cleaned, http_auth=HTTPAuthCredential(url_parts.username)
        )
    else:
        return PoetryAuthConfig(url=parsed_and_cleaned, http_auth=None)
