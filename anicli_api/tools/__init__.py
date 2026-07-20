def __getattr__(name: str):
    # lazy submodule exports to avoid double-import RuntimeWarning when running
    # `python -m anicli_api.tools.dummy_cli` (PEP 562)
    if name == "cli":
        from anicli_api.tools.dummy_cli import cli

        return cli
    if name == "generate_playlist":
        from anicli_api.tools.m3u import generate_playlist

        return generate_playlist
    if name == "generate_asyncio_playlist":
        from anicli_api.tools.m3u import generate_asyncio_playlist

        return generate_asyncio_playlist
    raise AttributeError(f"module 'anicli_api.tools' has no attribute {name!r}")


__all__ = ["cli", "generate_asyncio_playlist", "generate_playlist"]
