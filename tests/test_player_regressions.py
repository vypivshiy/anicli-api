from unittest.mock import Mock, patch

import httpx

from anicli_api.player.aniboom import Aniboom
from anicli_api.player.cdnvideohub import video_playlist_from_vk_id


def test_aniboom_returns_only_available_manifest():
    parsed = Mock()
    parsed.parse.return_value = {"hls": "https://cdn.example/video.m3u8", "dash": None}

    with patch("anicli_api.player.aniboom.PageAniboom", return_value=parsed):
        videos = Aniboom(http=Mock(), a_http=Mock())._extract(httpx.Response(200, text="page"))

    assert len(videos) == 1
    assert videos[0].type == "m3u8"
    assert videos[0].url == "https://cdn.example/video.m3u8"


def test_aniboom_returns_empty_when_manifests_are_missing():
    parsed = Mock()
    parsed.parse.return_value = {"hls": None, "dash": None}

    with patch("anicli_api.player.aniboom.PageAniboom", return_value=parsed):
        videos = Aniboom(http=Mock(), a_http=Mock())._extract(httpx.Response(200, text="page"))

    assert videos == []


def test_cdnvideohub_video_headers_use_per_call_user_agent():
    response = {
        "sources": {
            "hlsUrl": "https://cdn.example/video.m3u8",
            "dashUrl": "https://cdn.example/video.mpd",
            "mpegHighUrl": "https://cdn.example/video.mp4",
        }
    }
    client = httpx.Client(headers={"User-Agent": "client-ua"}, transport=httpx.MockTransport(lambda _: None))
    try:
        with patch(
            "anicli_api.player.cdnvideohub.CdnVideoHubAPI.from_vkid",
            return_value=Mock(is_ok=True, value=response),
        ):
            videos = video_playlist_from_vk_id(client, "42", headers={"User-Agent": "request-ua"})
    finally:
        client.close()

    assert videos
    assert all(video.headers["User-Agent"] == "request-ua" for video in videos)
