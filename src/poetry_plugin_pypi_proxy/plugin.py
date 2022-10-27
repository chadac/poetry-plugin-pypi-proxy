from __future__ import annotations

import copy
import os

from cleo.io.io import IO
from cleo.io.outputs.output import Verbosity
from poetry.core.packages.package import Package
from poetry.core.semver.version import Version
from poetry.plugins.plugin import Plugin
from poetry.poetry import Poetry
from poetry.repositories.legacy_repository import LegacyRepository

from poetry_plugin_pypi_proxy.utils import generate_poetry_source_config, get_repo_id


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
        source_config = generate_poetry_source_config(proxy_url)
        proxy_url = source_config["url"]

        # Add debug message so that users are certain the substitution happens
        io.write_line(
            f"Disabling Pypi and substituting with proxy server at {proxy_url}.",
            verbosity=Verbosity.VERBOSE,
        )

        # Generate unique string for project root
        proxy_id = get_repo_id(proxy_url)

        poetry.config._config["repository"] = {proxy_id: source_config}
        # Set up the proxy as the default, remove
        poetry.pool._default = False
        poetry.pool.remove_repository("pypi")

        # resolve bug in old Poetry
        if "pypi" in poetry.pool._lookup:
            del poetry.pool._lookup["pypi"]

        # Add default repository
        poetry.pool.add_repository(
            LegacyProxyRepository(
                name=proxy_id, url=f"{proxy_url}simple/", config=poetry.config._config
            ),
            default=True,
        )

        # If this is a publish command to Pypi, we'll silenly redirect to the proxy
        if io.input.arguments["command"] == "publish" and not io.input.option(
            "repository"
        ):
            io.input.set_option("repository", proxy_id)
