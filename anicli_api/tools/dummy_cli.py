from typing import TYPE_CHECKING, Sequence, TypeVar
from anicli_api.base import BaseSource

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
    from anicli_api.player.base import Video

__all__ = ["cli"]

T = TypeVar("T")

HELP_ = """h - print help
s <query> - search by query
o - get ongoings
p <url> - extract videos from player url
"""


def _pretty_print(items: Sequence[T]):
    for i, item in enumerate(items):
        print(f"[{i + 1}] {item}")


def _choice(items: Sequence[T], input_state: str = "") -> T:
    _pretty_print(items)
    while True:
        ch = input(f"{input_state})> ")
        if ch.isdigit() and len(items) > int(ch) - 1:
            return items[int(ch) - 1]


def _generate_mpv_cmd(vid: "Video"):
    def _headers_to_str(headers: dict):
        result = []
        for k, v in headers.items():
            v = v.replace('"', '\\"')
            result.append(f'"{k}: {v}"')
        return ",".join(result)

    if vid.headers:
        return f'mpv "{vid.url}" --http-header-fields={_headers_to_str(vid.headers)}'
    return f'mpv "{vid.url}"'


def _search_entry(e: "BaseExtractor", q: str):
    res = e.search(q)
    if not _is_empty(res):
        return
    print("choice title")
    item: "BaseSearch" = _choice(res, "SEARCH")
    return _anime_entry(item.get_anime())


def _ongoing_entry(e: "BaseExtractor"):
    res = e.ongoing()
    if not _is_empty(res):
        return
    print("choice title")
    item: "BaseOngoing" = _choice(res, "ONGOING")
    return _anime_entry(item.get_anime())


def _is_empty(var: T) -> bool:
    if var:
        return True
    print("not found")
    return False


def _anime_entry(a: "BaseAnime"):
    eps = a.get_episodes()
    if not _is_empty(eps):
        return
    print(a)
    print("choice episode")
    item: "BaseEpisode" = _choice(eps, "EPISODE")

    s = item.get_sources()
    if not _is_empty(s):
        return

    print("choice source")
    item: "BaseSource" = _choice(s, "SOURCE")
    vids = item.get_videos()
    if not _is_empty(vids):
        return

    print("choice vids")
    vid: "Video" = _choice(vids, "VIDEO")
    print("QUALITY, HEADERS, URL")
    print(f"[{vid.quality}]", ", ".join([f"{k}={v}" for k, v in vid.headers.items()]) or None, vid.url)
    print("MPV DEBUG COMMAND:")
    print(_generate_mpv_cmd(vid))


def main(extractor: "BaseExtractor"):
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
                _search_entry(extractor, comma.lstrip("s "))
            elif comma == "o":
                _ongoing_entry(extractor)
            elif comma.startswith("p "):
                url = comma.lstrip("p ")
                videos = BaseSource(title="_", url=url).get_videos()
                print(*[f"{v.url} {v.quality} {v.headers}" for v in videos], sep="\n")
        except (KeyboardInterrupt, EOFError):
            exit(0)


def cli(extractor: "BaseExtractor"):
    """minimal dummy cli app for interactive manual tests

    usage:

        >>> from anicli_api.tools import cli
        >>> from anicli_api.source.animego import Extractor
        >>> cli(Extractor())

    """
    main(extractor)
