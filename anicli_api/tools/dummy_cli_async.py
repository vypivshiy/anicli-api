from typing import TYPE_CHECKING, TypeVar
import asyncio

from anicli_api.typing import MutableSequence
from anicli_api.base import BaseSource

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
    from anicli_api.player.base import Video

__all__ = ["async_cli"]

T = TypeVar("T")

HELP_ = """h - print help
s <query> - search by query
o - get ongoings
p <url> - extract videos from player url
"""


def _pretty_print(items: MutableSequence[T]):
    for i, item in enumerate(items):
        print(f"[{i + 1}] {item}")


def _choice(items: MutableSequence[T], input_state: str = "") -> T:
    _pretty_print(items)
    while True:
        ch = input(f"{input_state})> ")
        if ch.isdigit() and len(items) > int(ch) - 1:
            return items[int(ch) - 1]


def _generate_mpv_cmd(vid: "Video"):
    def _headers_to_mpv_opts(headers: dict):
        result = []
        referrer = "--referrer=" + '"' + headers.pop("Referrer") + '"' if headers.get("Referrer") else ""
        user_agent = "--user-agent=" + '"' + headers.pop("User-Agent") + '"' if headers.get("User-Agent") else ""
        for k, v in headers.items():
            v = v.replace('"', '\\"')
            result.append(f'"{k}: {v}"')
        if result:
            return f"{user_agent} {referrer} --http-header-fields={','.join(result)}"
        return f"{user_agent} {referrer}"

    if vid.headers:
        return f'mpv "{vid.url}" {_headers_to_mpv_opts(vid.headers)}'
    return f'mpv "{vid.url}"'


async def _search_entry(e: "BaseExtractor", q: str):
    res = await e.a_search(q)
    if not _is_empty(res):
        return
    print("choice title")
    item: "BaseSearch" = _choice(res, "SEARCH")
    anime = await item.a_get_anime()
    return await _anime_entry(anime)


async def _ongoing_entry(e: "BaseExtractor"):
    res = await e.a_ongoing()
    if not _is_empty(res):
        return
    print("choice title")
    item: "BaseOngoing" = _choice(res, "ONGOING")
    anime = await item.a_get_anime()
    return await _anime_entry(anime)


def _is_empty(var: T) -> bool:
    if var:
        return True
    print("not found")
    return False


async def _anime_entry(a: "BaseAnime"):
    eps = await a.a_get_episodes()
    if not _is_empty(eps):
        return
    print(a.title)
    print("=" * len(a.title))
    if a.description:
        print(a.description)
    print("choice episode")
    item: "BaseEpisode" = _choice(eps, "EPISODE")

    s = await item.a_get_sources()
    if not _is_empty(s):
        return

    print("choice source")
    item: "BaseSource" = _choice(s, "SOURCE")
    vids = await item.a_get_videos()
    if not _is_empty(vids):
        return

    print("choice vids")
    vid: "Video" = _choice(vids, "VIDEO")
    print("QUALITY, HEADERS, URL")

    print(f"[{vid.quality}]", ", ".join([f"{k}={v}" for k, v in vid.headers.items()]) or None, vid.url)
    print("MPV DEBUG COMMAND:")
    print(_generate_mpv_cmd(vid))


async def main(extractor: "BaseExtractor"):
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
                await _search_entry(extractor, comma.lstrip("s "))
            elif comma == "o":
                await _ongoing_entry(extractor)
            elif comma.startswith("p "):
                url = comma.lstrip("p ")
                videos = await BaseSource(title="_", url=url).a_get_videos()
                print(*[f"{v.url} {v.quality} {v.headers}" for v in videos], sep="\n")
        except (KeyboardInterrupt, EOFError):
            exit(0)


def async_cli(extractor: "BaseExtractor"):
    """minimal dummy async cli app for interactive manual tests

    usage:

        >>> from anicli_api.tools.dummy_cli_async import async_cli
        >>> from anicli_api.source.animego import Extractor
        >>> async_cli(Extractor())

    """
    asyncio.run(main(extractor))


def __get_available_sources():
    source_dir = Path(__file__).parent.parent / "source"
    return [p.stem for p in source_dir.glob("[!_]*.py")]


# shortcut cli runner
# in project: python anicli_api/tools/dummy_cli_async.py <extractor name>
# in installed lib: python -m anicli_api.tools.dummy_cli_async <extractor name>
if __name__ == "__main__":
    import importlib, sys  # noqa
    from pathlib import Path

    if len(sys.argv) < 2:
        sources = __get_available_sources()
        print("USAGE: python -m anicli_api.tools <extractor name>")
        print(f"Available modules: {', '.join(sources)}")
        sys.exit(1)

    module_name = sys.argv[1]
    full_path = f"anicli_api.source.{module_name}"
    try:
        module = importlib.import_module(full_path)
        extractor_cls = getattr(module, "Extractor", None)
        if not extractor_cls:
            print(f"ERROR: 'Extractor' class not defined in {full_path}")
            sys.exit(1)
        extractor = extractor_cls()
        async_cli(extractor)
    except ImportError:
        sources = __get_available_sources()
        print(f"ERROR: module '{module_name}' not founded in source.")
        print(f"Available modules: {', '.join(sources)}")
        sys.exit(1)
    except Exception as e:
        raise e
