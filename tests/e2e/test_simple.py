from __future__ import annotations

import pytest

from typing import TYPE_CHECKING
from multiprocessing import Process
import shutil
import socket
import signal
import pip._internal.cli.main as pip
import os
from pathlib import Path
import sys
import http.server
import socketserver
import tempfile
import subprocess

from poetry.plugins.application_plugin import ApplicationPlugin
from poetry.plugins.plugin_manager import PluginManager
from poetry.console.application import Application
from poetry_plugin_pypi_proxy.plugin import PypiProxyPlugin
from cleo.testers.application_tester import ApplicationTester


if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from pytest_httpserver import HTTPServer
    from poetry.poetry import Poetry


class MockApplication(Application):
    @property
    def poetry(self) -> Poetry:
        if self._poetry is not None:
            return self._poetry
        _poetry = super().poetry
        root = _poetry._pyproject._file.parent
        _poetry.config._config["cache-dir"] = str(root / ".virtualenvs")
        return _poetry

    def _load_plugins(self, io: IO | None = None) -> None:
        if self._plugins_loaded:
            return

        manager = PluginManager(ApplicationPlugin.group)
        manager.add_plugin(PypiProxyPlugin())
        # manager.activate(self.poetry, io)

        self._plugins_loaded = True


@pytest.fixture(scope="session")
def sample_dependency() -> Path:
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path) / "sample-dependency"
        shutil.copytree(Path(__file__).parent / "sample-dependency", tmp_path)
        for version in ["0.0.1", "0.0.2"]:
            subprocess.run([sys.executable, "setup.py", "bdist_wheel"],
                           cwd=tmp_path,
                           env={"PKG_VERSION": version, "SOURCE_DATE_EPOCH": "1451635200"})
        yield tmp_path


@pytest.fixture(scope="session")
def pypicache(sample_dependency: Path) -> Path:
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        (tmp_path / "simple").mkdir()
        shutil.copytree(sample_dependency / "dist", tmp_path / "simple" / "sample-dependency")
        yield tmp_path


def start_server(root: Path, port: int) -> None:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)

    with socketserver.TCPServer(
            ("", port),
            Handler
    ) as httpd:
        httpd.serve_forever()

@pytest.fixture
def pypiproxy(pypicache: Path) -> int:
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    config = {
        "root": pypicache,
        "port": port,
    }
    p = Process(
        target=start_server,
        kwargs=config,
    )
    p.start()
    yield port
    p.kill()
    p.join()


@pytest.fixture(scope="function")
def poetry(tmp_path: Path, mocker: MockerFixture, pypiproxy: int) -> LocalAppTester:
    project_path = tmp_path / "sample-project"
    shutil.copytree(Path(__file__).parent / "sample-project", project_path)
    mocker.patch.dict(
       os.environ, {
           "PIP_INDEX_URL": f"http://127.0.0.1:{pypiproxy}/simple/",
           "VIRTUAL_ENV": "",
       }
    )
    mocker.patch("pathlib.Path.cwd", return_value=project_path)
    poetry = ApplicationTester(MockApplication())
    yield poetry


def test_install(poetry: LocalAppTester) -> None:
    exit_code = poetry.execute("install")
    assert exit_code == 0


def test_update(poetry: LocalAppTester) -> None:
    exit_code = poetry.execute("update")
    assert exit_code == 0


def test_lock(poetry: LocalAppTester) -> None:
    exit_code = poetry.execute("lock")
    assert exit_code == 0


def test_publish(poetry: LocalAppTester) -> None:
    exit_code = poetry.execute("publish")
    assert exit_code == 0
