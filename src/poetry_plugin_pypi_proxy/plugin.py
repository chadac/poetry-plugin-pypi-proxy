from __future__ import annotations

import copy
import os

from cleo.io.io import IO
from cleo.io.outputs.output import Verbosity
from poetry.core.packages.package import Package
from poetry.plugins.plugin import Plugin
from poetry.poetry import Poetry
from poetry.repositories.legacy_repository import LegacyRepository

from poetry_plugin_pypi_proxy.utils import (
    POETRY_VERSION,
    Version,
    generate_poetry_auth_config,
    get_repo_id,
)


class LegacyProxyRepository(LegacyRepository):
    """
    Alternative repository that strips URL information from packages.

    Mainly used to ensure the lockfile looks as if it were pulled
    directly from Pypi.
    """

    def package(
        self, name: str, version: Version, extras: list[str] | None = None
    ) -> Package:
        """
        Pull package information without proxy-specific info.

        :param name: Package name
        :param version: Package version
        :param extras: List of requires extras to install
        :returns: Package metadata
        """
        package = copy.copy(super().package(name, version, extras))

        # Eliminate any metadata that would cause the proxy url to
        # appear in the lockfile
        package._source_type = None
        package._source_reference = None
        package._source_url = None

        return package


class PypiProxyPlugin(Plugin):
    """
    Main plugin logic for substituting downloading, caching and publishing.
    """

    def activate(self, poetry: Poetry, io: IO) -> None:
        """
        Run when `poetry` executes.
        """
        # Get environment pip index URL (non-simple endpoint)
        proxy_url = os.environ.get("PIP_INDEX_URL")

        # If the PIP_INDEX_URL is not set, we're going to assume the particular
        # project does not need to be proxied.
        if proxy_url is None:
            io.write_line(
                "No PIP_INDEX_URL set, so no Pypi proxy will be configured.",
                verbosity=Verbosity.VERBOSE,
            )
            return

        # Parse the proper for PIP_INDEX_URL but not for publishing.
        auth_config = generate_poetry_auth_config(proxy_url)
        proxy_url = auth_config.url

        # Add debug message so that users are certain the substitution happens
        io.write_line(
            f"Disabling Pypi and substituting with proxy server at {proxy_url}.",
            verbosity=Verbosity.VERBOSE,
        )

        # Generate unique string for project root
        proxy_id = get_repo_id(proxy_url)

        # Create entries in the config for the repo and Auth if we have it
        poetry.config._config["repositories"] = {proxy_id: {"url": auth_config.url}}
        if auth_config.http_auth is not None:
            poetry.config._config["http-basic"] = poetry.config._config.get(
                "http-basic", {}
            )
            poetry.config._config["http-basic"][proxy_id] = {
                "username": auth_config.http_auth.username,
                "password": auth_config.http_auth.password,
            }

        # Set up the proxy as the default, remove
        poetry.pool._default = False
        if poetry.pool.has_repository("pypi"):
            poetry.pool.remove_repository("pypi")

        # resolve bug in old Poetry
        if POETRY_VERSION < (1, 2, 1):
            if "pypi" in poetry.pool._lookup:
                del poetry.pool._lookup["pypi"]

        # Add default repository
        poetry.pool.add_repository(
            LegacyProxyRepository(
                name=proxy_id, url=f"{proxy_url}/simple/", config=poetry.config
            ),
            default=True,
        )

        # If this is a publish command to Pypi, we'll silenly redirect to the proxy
        if io.input.arguments["command"] == "publish" and not io.input.option(
            "repository"
        ):
            io.input.set_option("repository", proxy_id)
