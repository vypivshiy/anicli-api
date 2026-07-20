from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Protocol, TypeVar, runtime_checkable

from anicli_api.base import BaseExtractor, BaseSource
from anicli_api.typing import MutableSequence

if TYPE_CHECKING:
    from anicli_api.base import (
        BaseAnime,
        BaseEpisode,
        BaseOngoing,
        BaseSearch,
    )
    from anicli_api.player.base import Video

__all__ = ["cli", "async_cli", "main"]

T = TypeVar("T")

HELP_ = """h - print help
s <query> - search by query
o - get ongoings
p <url> - extract videos from player url
"""


@runtime_checkable
class _Ops(Protocol):
    """uniform async interface over sync or async extractor methods"""

    async def search(self, query: str) -> MutableSequence[BaseSearch]: ...
    async def ongoing(self) -> MutableSequence[BaseOngoing]: ...
    async def get_anime(self, item: BaseSearch | BaseOngoing) -> BaseAnime: ...
    async def get_episodes(self, anime: BaseAnime) -> MutableSequence[BaseEpisode]: ...
    async def get_sources(self, episode: BaseEpisode) -> MutableSequence[BaseSource]: ...
    async def get_videos(self, source: BaseSource) -> MutableSequence[Video]: ...


_OpsFactory = Callable[[BaseExtractor], _Ops]


class _SyncOps:
    """adapter: expose sync extractor methods as coroutines"""

    def __init__(self, extractor: BaseExtractor) -> None:
        self._e = extractor

    async def search(self, query: str) -> MutableSequence[BaseSearch]:
        return self._e.search(query)

    async def ongoing(self) -> MutableSequence[BaseOngoing]:
        return self._e.ongoing()

    async def get_anime(self, item: BaseSearch | BaseOngoing) -> BaseAnime:
        return item.get_anime()

    async def get_episodes(self, anime: BaseAnime) -> MutableSequence[BaseEpisode]:
        return anime.get_episodes()

    async def get_sources(self, episode: BaseEpisode) -> MutableSequence[BaseSource]:
        return episode.get_sources()

    async def get_videos(self, source: BaseSource) -> MutableSequence[Video]:
        return source.get_videos()


class _AsyncOps:
    """adapter: delegate to a_* async extractor methods"""

    def __init__(self, extractor: BaseExtractor) -> None:
        self._e = extractor

    async def search(self, query: str) -> MutableSequence[BaseSearch]:
        return await self._e.a_search(query)

    async def ongoing(self) -> MutableSequence[BaseOngoing]:
        return await self._e.a_ongoing()

    async def get_anime(self, item: BaseSearch | BaseOngoing) -> BaseAnime:
        return await item.a_get_anime()

    async def get_episodes(self, anime: BaseAnime) -> MutableSequence[BaseEpisode]:
        return await anime.a_get_episodes()

    async def get_sources(self, episode: BaseEpisode) -> MutableSequence[BaseSource]:
        return await episode.a_get_sources()

    async def get_videos(self, source: BaseSource) -> MutableSequence[Video]:
        return await source.a_get_videos()


def _pretty_print(items: MutableSequence[T]) -> None:
    for i, item in enumerate(items):
        print(f"[{i + 1}] {item}")


def _choice(items: MutableSequence[T], input_state: str = "") -> T:
    _pretty_print(items)
    while True:
        ch = input(f"{input_state})> ")
        if ch.isdigit() and 0 <= int(ch) - 1 < len(items):
            return items[int(ch) - 1]


def _is_empty(var: T) -> bool:
    if var:
        return False
    print("not found")
    return True


def _generate_mpv_cmd(vid: Video) -> str:
    def _headers_to_mpv_opts(headers: dict[str, str]) -> str:
        result: list[str] = []
        referrer = '--referrer="' + headers.pop("Referrer") + '"' if headers.get("Referrer") else ""
        user_agent = '--user-agent="' + headers.pop("User-Agent") + '"' if headers.get("User-Agent") else ""
        for k, v in headers.items():
            v = v.replace('"', '\\"')
            result.append(f'"{k}: {v}"')
        if result:
            return f"{user_agent} {referrer} --http-header-fields={','.join(result)}"
        return f"{user_agent} {referrer}"

    if vid.headers:
        return f'mpv "{vid.url}" {_headers_to_mpv_opts(vid.headers)}'
    return f'mpv "{vid.url}"'


async def _search_entry(ops: _Ops, q: str) -> None:
    res = await ops.search(q)
    if _is_empty(res):
        return
    print("choice title")
    item = _choice(res, "SEARCH")
    anime = await ops.get_anime(item)
    await _anime_entry(anime, ops)


async def _ongoing_entry(ops: _Ops) -> None:
    res = await ops.ongoing()
    if _is_empty(res):
        return
    print("choice title")
    item = _choice(res, "ONGOING")
    anime = await ops.get_anime(item)
    await _anime_entry(anime, ops)


async def _anime_entry(anime: BaseAnime, ops: _Ops) -> None:
    eps = await ops.get_episodes(anime)
    if _is_empty(eps):
        return
    print(anime.title)
    print("=" * len(anime.title))
    if anime.description:
        print(anime.description)
    print("choice episode")
    episode = _choice(eps, "EPISODE")

    sources = await ops.get_sources(episode)
    if _is_empty(sources):
        return

    print("choice source")
    source = _choice(sources, "SOURCE")
    vids = await ops.get_videos(source)
    if _is_empty(vids):
        return

    print("choice vids")
    vid = _choice(vids, "VIDEO")
    print("QUALITY, HEADERS, URL")
    print(
        f"[{vid.quality}]",
        ", ".join([f"{k}={v}" for k, v in vid.headers.items()]) or None,
        vid.url,
    )
    print("MPV DEBUG COMMAND:")
    print(_generate_mpv_cmd(vid))


async def main(extractor: BaseExtractor, ops_factory: _OpsFactory) -> None:
    ops = ops_factory(extractor)
    print("load:", extractor.BASE_URL)
    print("type h for get all commands. PRESS ctrl+c for exit")
    while True:
        try:
            comma = input("> ")
            if not comma:
                continue
            if comma.lower() == "h":
                print(HELP_)
            elif comma.startswith("s "):
                await _search_entry(ops, comma.removeprefix("s "))
            elif comma == "o":
                await _ongoing_entry(ops)
            elif comma.startswith("p "):
                url = comma.removeprefix("p ")
                videos = await ops.get_videos(BaseSource(title="_", url=url))
                print(*[f"{v.url} {v.quality} {v.headers}" for v in videos], sep="\n")
        except (KeyboardInterrupt, EOFError):
            return


def cli(extractor: BaseExtractor) -> None:
    """minimal dummy sync cli app for interactive manual tests

    usage:

        >>> from anicli_api.tools.dummy_cli import cli
        >>> from anicli_api.source.animego import Extractor
        >>> cli(Extractor())

    """
    asyncio.run(main(extractor, _SyncOps))


def async_cli(extractor: BaseExtractor) -> None:
    """minimal dummy async cli app for interactive manual tests

    usage:

        >>> from anicli_api.tools.dummy_cli import async_cli
        >>> from anicli_api.source.animego import Extractor
        >>> async_cli(Extractor())

    """
    asyncio.run(main(extractor, _AsyncOps))


def _get_available_sources() -> list[str]:
    source_dir = Path(__file__).parent.parent / "source"
    return [p.stem for p in source_dir.glob("[!_]*.py")]


# shortcut cli runner
# in project: python anicli_api/tools/dummy_cli.py <extractor name> [--async]
# in installed lib: python -m anicli_api.tools.dummy_cli <extractor name> [--async]
if __name__ == "__main__":
    import importlib

    args = sys.argv[1:]
    use_async = "--async" in args
    args = [a for a in args if a != "--async"]

    if not args:
        sources = _get_available_sources()
        print("USAGE: python -m anicli_api.tools.dummy_cli <extractor name> [--async]")
        print(f"Available modules: {', '.join(sources)}")
        sys.exit(1)

    module_name = args[0]
    full_path = f"anicli_api.source.{module_name}"
    try:
        module = importlib.import_module(full_path)
        extractor_cls = getattr(module, "Extractor", None)
        if not extractor_cls:
            print(f"ERROR: 'Extractor' class not defined in {full_path}")
            sys.exit(1)
        extractor = extractor_cls()
        if use_async:
            async_cli(extractor)
        else:
            cli(extractor)
    except ImportError:
        sources = _get_available_sources()
        print(f"ERROR: module '{module_name}' not founded in source.")
        print(f"Available modules: {', '.join(sources)}")
        sys.exit(1)
