from typing import Optional, Tuple, Type

import httpx
import pytest

from anicli_api.player import (
    Aniboom,
    AnimeJoy,
    CsstOnline,
    Dzen,
    Kodik,
    MailRu,
    Nuum,
    OkRu,
    SibNet,
    SovietRomanticaPlayer,
    VkCom,
)
from anicli_api.player.base import BaseVideoExtractor


# for stub types check set ("mp4", "m3u8", "mpd", "audio", "webm")
# for stub count check set -1
@pytest.mark.parametrize(
    "player, url, count, types, index",
    [
        # t-party backend issue maybe return 1 or 2 videos --------------------------v------------vvv
        (Aniboom, "https://aniboom.one/embed/6BmMbB7MxWO?episode=1&translation=30", -1, ("m3u8", "mpd"), 0),
        (Kodik, "https://kodik.info/seria/1133512/04d5f7824ba3563bd78e44a22451bb45/720p", 3, ("m3u8",), 0),
        (CsstOnline, "https://csst.online/embed/487794", 4, ("mp4",), 0),
        (
            Dzen,
            "https://dzen.ru/embed/vh1fMeui3d3Y?from_block=partner&from=zen&mute=1&autoplay=0&tv=0",
            3,
            ("mpd", "m3u8", "audio"),
            -1,
        ),
        (MailRu, "https://my.mail.ru/video/embed/358279802395848306", 2, ("mp4",), 0),
        (OkRu, "https://ok.ru/videoembed/4998442453635", 6, ("mp4",), 0),
        (SibNet, "https://video.sibnet.ru/shell.php?videoid=4779967", 1, ("mp4",), 0),
        (
            SovietRomanticaPlayer,
            "https://scu3.sovetromantica.com/anime/1253_100-man-no-inochi-no-ue-ni-ore-wa-tatteiru-2nd-season/episodes/subtitles/episode_1/episode_1.m3u8",
            1,
            ("m3u8",),
            0,
        ),
        (VkCom, "https://vk.com/video_ext.php?oid=793268683&id=456239019&hash=0f28589bfca114f7", 5, ("mp4",), 0),
        (Nuum, "https://nuum.ru/embed/record/1610248", 1, ("m3u8",), 0),
    ],
)
def test_sync_video_extractor(
    player: Type[BaseVideoExtractor], url: str, count: int, types: Tuple[str, ...], index: int
):
    if (status := player().http.get(url).status_code) and status != 200:
        pytest.skip(f"Player {player.__name__} return [{status}] code.")

    videos = player().parse(url)
    # -1 - skip check
    assert len(videos) == count or count == -1

    assert all(v.type in types for v in videos)
    # check correct headers for play video in minimal configuration
    resp = httpx.head(videos[index].url, headers=videos[index].headers, follow_redirects=False)
    assert resp.is_success or resp.is_redirect


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "player, url, count, types, index",
    [
        # t-party backend issue maybe return 1 or 2 videos --------------------------v------------vvv
        (Aniboom, "https://aniboom.one/embed/6BmMbB7MxWO?episode=1&translation=30", -1, ("m3u8", "mpd"), 0),
        (Kodik, "https://kodik.info/seria/1133512/04d5f7824ba3563bd78e44a22451bb45/720p", 3, ("m3u8",), 0),
        (CsstOnline, "https://csst.online/embed/487794", 4, ("mp4",), 0),
        (
            Dzen,
            "https://dzen.ru/embed/vh1fMeui3d3Y?from_block=partner&from=zen&mute=1&autoplay=0&tv=0",
            3,
            ("mpd", "m3u8", "audio"),
            -1,
        ),
        (MailRu, "https://my.mail.ru/video/embed/358279802395848306", 2, ("mp4",), 0),
        (OkRu, "https://ok.ru/videoembed/4998442453635", 6, ("mp4",), 0),
        (SibNet, "https://video.sibnet.ru/shell.php?videoid=4779967", 1, ("mp4",), 0),
        (
            SovietRomanticaPlayer,
            "https://scu3.sovetromantica.com/anime/1253_100-man-no-inochi-no-ue-ni-ore-wa-tatteiru-2nd-season/episodes/subtitles/episode_1/episode_1.m3u8",
            1,
            ("m3u8",),
            0,
        ),
        (VkCom, "https://vk.com/video_ext.php?oid=793268683&id=456239019&hash=0f28589bfca114f7", 5, ("mp4",), 0),
        (Nuum, "https://nuum.ru/embed/record/1610248", 1, ("m3u8",), 0),
    ],
)
async def test_async_video_extractor(
    player: Type[BaseVideoExtractor], url: str, count: int, types: Tuple[str, ...], index: int
):
    status = (await player().a_http.get(url)).status_code
    if status != 200:
        pytest.skip(f"Player {player.__name__} return [{status}] code.")

    videos = await player().a_parse(url)
    # -1 - skip check
    assert len(videos) == count or count == -1

    assert all(v.type in types for v in videos)
    resp = await httpx.AsyncClient().head(videos[index].url, headers=videos[index].headers, follow_redirects=False)
    assert resp.is_success or resp.is_redirect


@pytest.mark.parametrize(
    "extractor, url",
    (
        (Nuum(), "https://nuum.ru/embed/record/1549072"),
        (Kodik(), "https://kodik.info/seria/310427/09985563d891b56b1e9b01142ae11872/720p"),
    ),
)
def test_not_found_video_url(extractor, url):
    assert len(extractor.parse(url)) == 0


def test_animejoy():
    # This video extractor is only relevant for ONGOINGS
    # (After release, videos are deleted from the servers).
    # Written this TEST CASE to avoid rewriting relevant source
    videos = AnimeJoy().parse(
        "https://animejoy.ru/player/playerjs.html?file=[1080p]https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-1080.mp4,"
        "[360p]https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-360.mp4"
    )

    assert len(videos) == 2
    assert all(v.type in ("mp4",) for v in videos)
