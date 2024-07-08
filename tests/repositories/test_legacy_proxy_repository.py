from __future__ import annotations

import shutil
import urllib.parse as urlparse
from pathlib import Path

from poetry.repositories.link_sources.html import HTMLPage

from poetry_plugin_pypi_proxy.plugin import LegacyProxyRepository
from poetry_plugin_pypi_proxy.utils import Version


class MockRepository(LegacyProxyRepository):
    FIXTURES = Path(__file__).parent / "fixtures" / "legacy"

    def __init__(self) -> None:
        super().__init__("proxy", url="http://legacy.foo.bar", disable_cache=True)

    def _get_page(self, name: str) -> HTMLPage | None:
        fixture = self.FIXTURES / (name + ".html")
        if not fixture.exists():
            return None

        with fixture.open(encoding="utf-8") as f:
            return HTMLPage(self._url + "/" + name + ".html", f.read())

    def _download(self, url: str, dest: Path) -> None:
        filename = urlparse.urlparse(url).path.rsplit("/")[-1]
        filepath = self.FIXTURES.parent / "pypi.org" / "dists" / filename

        shutil.copyfile(str(filepath), dest)


def test_package_metadata_is_removed():
    repo = MockRepository()
    package = repo.package("black", Version.parse("21.11b0"))
    assert package._source_type is None
    assert package._source_reference is None
    assert package._source_url is None
