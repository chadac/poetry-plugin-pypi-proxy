from poetry_plugin_pypi_proxy.utils import parse_url


def test_parse_url():
    input = [
        "http://proxy.org/pypi/simple",
        "http://proxy.org/pypi/simple/",
        "http://proxy.org/pypi/simple/simple",
        "http://proxy.org/pypi/simple/simple/",
    ]
    expected = [
        "http://proxy.org/pypi/",
        "http://proxy.org/pypi/",
        "http://proxy.org/pypi/simple/",
        "http://proxy.org/pypi/simple/",
    ]

    for index in range(len(input)):
        actual = parse_url(input[index])
        assert actual == expected[index]
