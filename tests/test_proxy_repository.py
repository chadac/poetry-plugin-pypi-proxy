from poetry_plugin_pypi_proxy.plugin import PypiProxyPlugin


def test_repository_urls():
    plugin = PypiProxyPlugin()
    input = [
        "http://proxy.org/pypi/simple",
        "http://proxy.org/pypi/simple/",
        "http://proxy.org/pypi/simple/simple",
        "http://proxy.org/pypi/simple/simple/"
    ]
    expected = [
        "http://proxy.org/pypi/",
        "http://proxy.org/pypi/",
        "http://proxy.org/pypi/simple/",
        "http://proxy.org/pypi/simple/"
    ]
    
    for index in range(len(input)):
        actual = plugin.parse_url(input[index])
        assert actual == expected[index]
