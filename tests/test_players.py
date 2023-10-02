import pytest

from anicli_api.player import (
    Aniboom,
    AnimeJoy,
    CsstOnline,
    Dzen,
    Kodik,
    MailRu,
    OkRu,
    SibNet,
    SovietRomanticaPlayer,
    VkCom,
)


def test_aniboom():
    url = "https://aniboom.one/embed/6BmMbB7MxWO?episode=1&translation=30"
    status = Aniboom().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = Aniboom().parse(url)
    assert len(videos) == 2
    assert videos[0].headers == {
        "Accept-Language": "ru-RU",
        "Origin": "https://aniboom.one",
        "Referer": "https://aniboom.one/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    }
    assert all([v.type in ("mpd", "m3u8") for v in videos])


def test_kodik():
    url = "https://kodik.info/seria/1133512/04d5f7824ba3563bd78e44a22451bb45/720p"
    status = Kodik().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = Kodik().parse(url)
    assert len(videos) == 3
    assert videos[0].headers == {}
    assert all([v.type == "m3u8" for v in videos])


def test_animejoy():
    url = """https://animejoy.ru/player/playerjs.html?file=[1080p]https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-1080.mp4,[360p]https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-360.mp4"""
    videos = AnimeJoy().parse(url)
    assert len(videos) == 2
    assert all([v.type == "mp4" for v in videos])


def test_csst():
    url = "https://csst.online/embed/487794"
    status = CsstOnline().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = CsstOnline().parse(url)
    assert len(videos) == 4
    assert all([v.type == "mp4" for v in videos])


def test_dzen():
    url = "https://dzen.ru/embed/vh1fMeui3d3Y?from_block=partner&from=zen&mute=1&autoplay=0&tv=0"
    status = Dzen().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = Dzen().parse(url)
    print()
    assert len(videos) == 3
    assert all([v.type in ("mpd", "m3u8", "audio") for v in videos])


def test_mailru():
    url = "https://my.mail.ru/video/embed/358279802395848306"
    status = MailRu().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = MailRu().parse(url)
    assert len(videos) == 2
    assert all([v.type == "mp4" for v in videos])


def test_okru():
    url = "https://ok.ru/videoembed/4998442453635"
    status = OkRu().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = OkRu().parse(url)
    assert len(videos) == 6
    assert all([v.type == "mp4" for v in videos])


def test_sibnet():
    url = "https://video.sibnet.ru/shell.php?videoid=4779967"
    status = SibNet().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = SibNet().parse(url)
    assert len(videos) == 1
    assert videos[0].type == "mp4"


def test_sovetromantica():
    url = "https://scp1.sovetromantica.com/anime/1368_akuyaku-reijou-nanode-last-boss-wo-kattemimashita/episodes/subtitles/episode_1/episode_1.m3u8"
    status = SovietRomanticaPlayer().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = SovietRomanticaPlayer().parse(url)
    assert len(videos) == 1
    assert videos[0].type == "m3u8"


def test_vkcom():
    url = "https://vk.com/video_ext.php?oid=793268683&id=456239019&hash=0f28589bfca114f7"
    status = VkCom().http.get(url).status_code
    if status != 200:
        pytest.skip(f"Player return [{status}] code")
    videos = VkCom().parse(url)
    assert len(videos) == 5
    assert all([v.type == "mp4" for v in videos])
