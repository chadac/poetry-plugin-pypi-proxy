from __future__ import annotations

import pytest
from poetry.utils.password_manager import HTTPAuthCredential

from poetry_plugin_pypi_proxy.utils import (
    PoetryAuthConfig,
    generate_poetry_auth_config,
    parse_url,
)


@pytest.mark.parametrize(
    ["input_urls", "expected_url"],
    [
        (
            [
                "http://proxy.org/pypi",
                "http://proxy.org/pypi/",
                "http://proxy.org/pypi/simple",
                "http://proxy.org/pypi/simple/",
            ],
            "http://proxy.org/pypi",
        ),
        (
            [
                "http://proxy.org/pypi/simple/simple",
                "http://proxy.org/pypi/simple/simple/",
            ],
            "http://proxy.org/pypi/simple",
        ),
    ],
)
def test_parse_url(input_urls: list[str], expected_url: str) -> None:
    for input_url in input_urls:
        actual_url = parse_url(input_url)
        assert actual_url == expected_url


@pytest.mark.parametrize(
    ["input_url", "expected_output"],
    [
        (
            "http://fake:faked@proxy.org/pypi/simple",
            PoetryAuthConfig(
                url="http://proxy.org/pypi",
                http_auth=HTTPAuthCredential(username="fake", password="faked"),
            ),
        ),
        (
            "http://fake:faked@proxy.org:8080/pypi/simple",
            PoetryAuthConfig(
                url="http://proxy.org:8080/pypi",
                http_auth=HTTPAuthCredential(username="fake", password="faked"),
            ),
        ),
        (
            "http://fake@proxy.org/pypi/simple",
            PoetryAuthConfig(
                url="http://proxy.org/pypi",
                http_auth=HTTPAuthCredential(username="fake"),
            ),
        ),
    ],
)
def test_generate_poetry_source_config(
    input_url: str, expected_output: PoetryAuthConfig
) -> None:
    actual = generate_poetry_auth_config(input_url)
    assert actual == expected_output


def test_no_user_name() -> None:
    with pytest.raises(ValueError):
        generate_poetry_auth_config("://proxy.org/pypi/simple")
