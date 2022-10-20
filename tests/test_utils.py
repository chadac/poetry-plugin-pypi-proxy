from poetry_plugin_pypi_proxy.utils import parse_url


def test_parse_url():
    input_urls = [
        "http://proxy.org/pypi/simple",
        "http://proxy.org/pypi/simple/",
        "http://proxy.org/pypi/simple/simple",
        "http://proxy.org/pypi/simple/simple/",
    ]
    expected_urls = [
        "http://proxy.org/pypi/",
        "http://proxy.org/pypi/",
        "http://proxy.org/pypi/simple/",
        "http://proxy.org/pypi/simple/",
    ]

    for input_url, expected_url in zip(input_urls, expected_urls):
        actual_url = parse_url(input_url)
        assert actual_url == expected_url
