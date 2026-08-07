"""Shared fixtures and config for e2e tests.

e2e tests hit REAL network. Skipped by default; enable via
`pytest -m e2e` or `--run-e2e` flag, or run `scripts/tests.{ps1,sh}`.

Configure without touching library code via env:

    ANICLI_PROXY=socks5://user:pass@host:1080   # socks5/http(s) proxy (httpx[socks] already installed)
    ANICLI_TEST_QUERY=lain                       # override default search query
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional, TypedDict
from urllib.parse import urlparse

import pytest
from attrs import frozen

from anicli_api._http import HEADERS, BaseHTTPAsync, BaseHTTPSync

if TYPE_CHECKING:
    from httpx import AsyncClient, Client

    from anicli_api.player.base import Video

# env-driven config (read once at import)
PROXY: Optional[str] = os.environ.get("ANICLI_PROXY") or None

VALID_VIDEO_TYPES: tuple[str, ...] = ("mp4", "m3u8", "mpd", "audio", "webm")
# quality 0 = audio-only
VALID_QUALITIES: tuple[int, ...] = (0, 144, 240, 360, 480, 720, 1080, 2160)

# how long to wait for the video probe (connect + first byte)
VIDEO_PROBE_TIMEOUT: float = 15.0

# type aliases for factory fixtures
SyncClientFactory = Callable[[Optional[dict[str, str]]], "Client"]
AsyncClientFactory = Callable[[Optional[dict[str, str]]], "AsyncClient"]
VideoChecker = Callable[["Video"], None]


class HttpKwargs(TypedDict):
    """kwargs dict consumed by BaseExtractor(http_client=..., http_async_client=...)."""

    http_client: "Client"
    http_async_client: "AsyncClient"


@frozen
class HttpBundle:
    """Paired httpx clients (proxy from env) + Extractor-kwargs shortcut.

    Use ``Extractor(**bundle.extractor_kwargs)`` for sources and
    ``Player(http=bundle.sync, a_http=bundle.async_)`` for players.
    """

    sync: "Client"
    async_: "AsyncClient"

    @property
    def extractor_kwargs(self) -> HttpKwargs:
        return {"http_client": self.sync, "http_async_client": self.async_}


# --------------------------------------------------------------------------------------------------
# pytest hooks: marker registration + skip-by-default
# --------------------------------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: hits real network, opt-in")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    # honour explicit `-m e2e` too: if marker filter active, do not force-skip
    mark_filter = config.getoption("-m") or ""
    if config.getoption("--run-e2e") or "e2e" in mark_filter:
        return

    skip = pytest.mark.skip(reason="e2e test; run via `pytest -m e2e` or --run-e2e")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="run e2e tests (hit real network)",
    )


@pytest.fixture
def event_loop_policy():
    """Use SelectorEventLoop on Windows.

    The default ProactorEventLoop leaks ``_ProactorBasePipeTransport.__del__``
    ``RuntimeError: Event loop is closed`` noise when an httpx AsyncClient is GC'd
    after the loop closes (happens for source tests that don't ``async with`` the
    client). Selector loop has no proactor pipes -> no such __del__ path.
    """
    if sys.platform == "win32":
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


# --------------------------------------------------------------------------------------------------
# client factories (for custom-headers case, e.g. Bearer auth)
# --------------------------------------------------------------------------------------------------


def _build_kwargs(extra_headers: Optional[dict[str, str]] = None) -> dict[str, Any]:
    kw: dict[str, Any] = {}
    if PROXY:
        kw["proxy"] = PROXY
    if extra_headers:
        # merge over defaults so UA / x-requested-with are preserved
        merged = HEADERS.copy()
        merged.update({k.lower(): v for k, v in extra_headers.items()})
        kw["headers"] = merged
    return kw


@pytest.fixture
def build_sync_client() -> SyncClientFactory:
    """factory: build a sync httpx Client with env proxy + optional extra headers."""

    def _factory(extra_headers: Optional[dict[str, str]] = None) -> "Client":
        return BaseHTTPSync(**_build_kwargs(extra_headers))

    return _factory


@pytest.fixture
def build_async_client() -> AsyncClientFactory:
    """factory: build an async httpx AsyncClient with env proxy + optional extra headers."""

    def _factory(extra_headers: Optional[dict[str, str]] = None) -> "AsyncClient":
        return BaseHTTPAsync(**_build_kwargs(extra_headers))

    return _factory


# --------------------------------------------------------------------------------------------------
# pre-built client bundle
# --------------------------------------------------------------------------------------------------


@pytest.fixture
def http_bundle(
    build_sync_client: SyncClientFactory,
    build_async_client: AsyncClientFactory,
) -> Iterator[HttpBundle]:
    """Pre-built (sync, async) client pair with env proxy + default headers.

    Function-scoped: several players do ``async with self.a_http`` which closes the
    client, so it must not be shared across tests. Sync client is closed at teardown
    (releases pooled connections); async client relies on GC.
    """
    bundle = HttpBundle(sync=build_sync_client(None), async_=build_async_client(None))
    yield bundle
    bundle.sync.close()


# --------------------------------------------------------------------------------------------------
# assertions helper
# --------------------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def assert_video_reachable() -> Iterator[VideoChecker]:
    """assert a Video is actually reachable, not just structurally well-formed.

    Strategy: GET-stream the url with ``Range: bytes=0-0`` so the server sends a
    single byte (206 Partial Content) instead of buffering the whole file — this
    dramatically cuts TTFB on CDNs that prepare the full response before serving.
    Read 1 byte, then close the stream.

    Why GET and not HEAD: many video CDNs reject HEAD (405/404) or break on signed
    urls; only GET proves the resource really serves bytes. Bandwidth is capped by
    the Range header + closing the response after 1 byte.

    ``video.headers`` is merged in — some CDNs (sibnet, aniboom) 403 without the
    Referer/Origin/Accept-Language they require.
    """
    # one client for the whole session; proxy from env, default UA headers
    client = BaseHTTPSync(**_build_kwargs(), timeout=VIDEO_PROBE_TIMEOUT)

    def _check(video: "Video") -> None:
        # structural checks first (cheap, catch parser regressions before hitting network)
        parsed = urlparse(video.url)
        assert parsed.scheme in ("http", "https"), f"bad url scheme: {video.url!r}"
        assert parsed.netloc, f"empty netloc: {video.url!r}"
        assert video.type in VALID_VIDEO_TYPES, f"bad video.type: {video.type!r}"
        assert video.quality in VALID_QUALITIES, f"bad video.quality: {video.quality!r}"
        assert isinstance(video.headers, dict), "video.headers must be dict"

        # reachability probe: ask for 1 byte via Range, read it, then drop the connection
        probe_headers = {"Range": "bytes=0-0"}
        probe_headers.update(video.headers)
        with client.stream("GET", video.url, headers=probe_headers) as resp:
            assert resp.status_code < 400, f"video url returned {resp.status_code} for {video.url}"
            chunk = next(resp.iter_bytes(1), b"")
            assert chunk, f"empty body from {video.url}"

    yield _check
    client.close()
