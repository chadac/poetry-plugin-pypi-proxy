from __future__ import annotations

import base64
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import setuptools.sandbox
from cleo.testers.application_tester import ApplicationTester
from poetry.console.application import Application
from poetry.plugins.application_plugin import ApplicationPlugin
from poetry.plugins.plugin_manager import PluginManager
from poetry.utils.password_manager import HTTPAuthCredential
from pytest_httpserver import HTTPServer, RequestHandler
from werkzeug.wrappers import Request, Response

from poetry_plugin_pypi_proxy.plugin import PypiProxyPlugin
from poetry_plugin_pypi_proxy.utils import POETRY_VERSION

if TYPE_CHECKING:
    from typing import Generator, Mapping

    from cleo.io.io import IO
    from poetry.poetry import Poetry
    from pytest_mock import MockerFixture


class MockApplication(Application):
    @property
    def poetry(self) -> Poetry:
        if self._poetry is not None:
            return self._poetry
        _poetry = super().poetry
        root = _poetry._pyproject.path.parent
        # root = _poetry._pyproject._file.parent
        _poetry.config._config["cache-dir"] = str(root / ".virtualenvs")
        return _poetry

    def _load_plugins(self, io: IO | None = None) -> None:
        if self._plugins_loaded:  # type: ignore
            return

        manager = PluginManager(ApplicationPlugin.group)
        manager.add_plugin(PypiProxyPlugin())

        self._plugins_loaded = True


class AuthHTTPServer(HTTPServer):
    def __init__(self, *args, auth: HTTPAuthCredential | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if auth is not None:
            token = base64.b64encode(
                f"{auth.username}:{auth.password}".encode()
            ).decode()
            self.auth = auth
            self.auth_header = f"Basic {token}"
        else:
            self.auth = None

    def respond_nohandler(self, request: Request, extra_message: str = ""):
        text = f"No handler found for request {request}.\nHeaders:\n{request.headers}"
        self.add_assertion(text + extra_message)
        return Response(
            f"No handler found for this request: {request.headers}",
            self.no_handler_status_code,
        )

    def expect_request(
        self, *args, headers: Mapping[str, str] | None = None, **kwargs
    ) -> RequestHandler:
        if self.auth:
            headers = dict(headers or {})
            headers["Authorization"] = self.auth_header
        return super().expect_request(*args, headers=headers, **kwargs)  # type: ignore


@pytest.fixture(
    params=[{"auth": None}, {"auth": HTTPAuthCredential("username", "password")}]
)
def httpserver(request) -> Generator[AuthHTTPServer, None, None]:
    server = AuthHTTPServer(**request.param)
    server.start()
    yield server
    server.clear()
    if server.is_running():
        server.stop()


@pytest.fixture(scope="session")
def sample_dependency() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "sample-dependency"
        shutil.copytree(Path(__file__).parent / "sample-dependency", tmp_path)
        for version in ["0.0.1", "0.0.2"]:
            setuptools.sandbox.run_setup(
                str(tmp_path / "setup.py"), [version, "--no-user-cfg", "bdist_wheel"]
            )
        yield tmp_path


@pytest.fixture
def sample_dependency_listing(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/simple/sample-dependency/").respond_with_data(
        """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Directory listing for /simple/sample-dependency/</title>
</head>
<body>
<h1>Directory listing for /simple/sample-dependency/</h1>
<hr>
<ul>
<li><a href="sample_dependency-0.0.1-py3-none-any.whl">sample_dependency-0.0.1-py3-none-any.whl</a></li>
<li><a href="sample_dependency-0.0.2-py3-none-any.whl">sample_dependency-0.0.2-py3-none-any.whl</a></li>
</ul>
<hr>
</body>
</html>
"""  # noqa: E501
    )


@pytest.fixture
def sample_dependency_v001(httpserver: HTTPServer, sample_dependency: Path) -> None:
    filename = "sample_dependency-0.0.1-py3-none-any.whl"
    httpserver.expect_request(
        f"/simple/sample-dependency/{filename}"
    ).respond_with_response(
        Response(
            (sample_dependency / "dist" / filename).open("rb").read(),
            direct_passthrough=True,
            content_type="application/octet-stream",
        )
    )


@pytest.fixture
def sample_dependency_v002(httpserver: HTTPServer, sample_dependency: Path) -> None:
    filename = "sample_dependency-0.0.2-py3-none-any.whl"
    httpserver.expect_request(
        f"/simple/sample-dependency/{filename}"
    ).respond_with_response(
        Response(
            (sample_dependency / "dist" / filename).open("rb").read(),
            direct_passthrough=True,
            content_type="application/octet-stream",
        )
    )


@pytest.fixture
def poetry(
    httpserver: AuthHTTPServer,
    mocker: MockerFixture,
    tmp_path: Path,
) -> Generator[ApplicationTester, None, None]:
    project_path = tmp_path / "sample-project"
    shutil.copytree(Path(__file__).parent / "sample-project", project_path)
    auth = httpserver.auth
    if auth is not None:
        index_url = (
            f"http://{auth.username}:{auth.password}"
            f"@localhost:{httpserver.port}/simple/"
        )
    else:
        index_url = f"http://localhost:{httpserver.port}/simple/"
    env_patch = {
        "PIP_INDEX_URL": index_url,
        "VIRTUAL_ENV": "",  # disable virtual env for proper creation
    }
    if os.name == "nt":  # windows-specific patches
        env_patch["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
        env_patch["HOME"] = os.environ.get("HOME", "")
    mocker.patch.dict(os.environ, env_patch)
    mocker.patch("pathlib.Path.cwd", return_value=project_path)
    # ignore hash conflicts
    mocker.patch("poetry.installation.executor.Executor._validate_archive_hash")
    poetry = ApplicationTester(MockApplication())
    yield poetry
    print(poetry.io.output.fetch(), file=sys.stdout)  # type: ignore
    print(poetry.io.error_output.fetch(), file=sys.stderr)  # type: ignore


@pytest.mark.skipif(POETRY_VERSION < (1, 3, 0), reason="requires poetry>1.3 or greater")
def test_install(
    httpserver: AuthHTTPServer,
    poetry: ApplicationTester,
    sample_dependency_listing: None,
    sample_dependency_v001: None,
) -> None:
    exit_code = poetry.execute("install -vv")
    httpserver.check_assertions()
    assert exit_code == 0


@pytest.mark.skipif(POETRY_VERSION < (1, 3, 0), reason="requires poetry>1.3 or greater")
def test_update(
    httpserver: AuthHTTPServer,
    poetry: ApplicationTester,
    sample_dependency_listing: None,
    sample_dependency_v001: None,
    sample_dependency_v002: None,
) -> None:
    exit_code = poetry.execute("update")
    httpserver.check_assertions()
    assert exit_code == 0


@pytest.mark.skipif(POETRY_VERSION < (1, 3, 0), reason="requires poetry>1.3 or greater")
def test_lock(
    httpserver: AuthHTTPServer,
    poetry: ApplicationTester,
    sample_dependency_listing: None,
    sample_dependency_v001: None,
    sample_dependency_v002: None,
) -> None:
    exit_code = poetry.execute("lock")
    httpserver.check_assertions()
    assert exit_code == 0


@pytest.mark.skipif(POETRY_VERSION < (1, 3, 0), reason="requires poetry>1.3 or greater")
def test_publish(
    httpserver: AuthHTTPServer,
    poetry: ApplicationTester,
) -> None:
    httpserver.expect_request(
        "/",
        method="POST",
    ).respond_with_json({})
    httpserver.expect_request(
        "/",
        method="POST",
    ).respond_with_json({})
    exit_code = poetry.execute("publish -vv")
    httpserver.check_assertions()
    assert exit_code == 0
