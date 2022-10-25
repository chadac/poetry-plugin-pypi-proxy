import pytest

from poetry_plugin_pypi_proxy.utils import parse_url


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
