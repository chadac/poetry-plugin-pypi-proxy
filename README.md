# poetry-plugin-pypi-proxy

This is a plugin that enables developers who use internal proxies of
Pypi to integrate their projects seamlessly with Poetry without
needing to build custom configurations for their proxy server.

The plugin operates intuitively -- users can onboard to this tooling
by installing the plugin and then setting `PIP_INDEX_URL` before
running Poetry commands.

It also runs silently, i.e., it will not pollute your `poetry.lock`
with the URL of your proxy server and `poetry publish` is
automatically redirected to the proxy as well.

## Usage

Start by installing Poetry with pipx:

    pipx install poetry
    poetry self add poetry-plugin-pypi-proxy[plugin]

If you have already installed poetry, you only need to run the second command.

Now, any Poetry project will automatically use the proxy server
specified by `PIP_INDEX_URL`. You may add this to your `rc` file
(`.bashrc`, `.zshrc`, `.envrc` with direnv, etc) or simply export it
in your terminal to get started.
