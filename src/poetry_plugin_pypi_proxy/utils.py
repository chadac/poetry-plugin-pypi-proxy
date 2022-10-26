import hashlib
import re


def get_repo_id(repo_url: str) -> str:
    """
    Generate a unique identifier for the proxy server.

    Note that this can change between clones of this project.  This
    is used silently when caching packages and for the publisher, so
    it should have no effect on your build processes.
    """
    key = hashlib.md5((repo_url).encode()).hexdigest()
    return f"pypi-proxy-{key}"


def parse_url(url: str) -> str:
    """Remove suffix from url appropriately so it can be used by the proxy object."""
    return re.sub("/?(simple/?)?$", "", url)
