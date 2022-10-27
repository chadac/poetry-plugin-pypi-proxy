from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

from typing_extensions import NotRequired, TypedDict


class PoetrySourceConfig(TypedDict):
    """
    This class is used for being able to represent what is needed for
    the source for Poetry
    """

    username: NotRequired[str]
    password: NotRequired[str]
    url: str


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


def generate_poetry_source_config(url: str) -> PoetrySourceConfig:
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
    cleaned_url = url_parts.scheme + "://" + url_parts.hostname + url_parts.path
    parsed_and_cleaned = parse_url(cleaned_url)
    if url_parts.username is not None and url_parts.password is not None:
        return PoetrySourceConfig(
            url=parsed_and_cleaned,
            username=url_parts.username,
            password=url_parts.password,
        )
    elif url_parts.username is not None and (
        url_parts.password == "" or url_parts.password is None
    ):
        return PoetrySourceConfig(url=parsed_and_cleaned, username=url_parts.username)
    else:
        return PoetrySourceConfig(url=parsed_and_cleaned)
