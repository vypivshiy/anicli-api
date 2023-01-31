from anicli_api.extractors.animego import Extractor


def test_animego_kodik():
    ex = Extractor()
    cmp_video_object = None
    for search_iter in ex.walk_search("lain"):
        assert search_iter.anime.url == "https://animego.org/anime/eksperimenty-leyn-1114"
        assert search_iter.anime.url == "https://animego.org/anime/eksperimenty-leyn-1114"
        if "kodik" in search_iter.video.url:
            if not cmp_video_object:
                cmp_video_object = search_iter.video
            assert cmp_video_object == search_iter.video
            sources = search_iter.video.get_source()
            assert sources[-1].type == "m3u8"
            assert sources[-1].quality == 720


def test_animego_aniboom():
    ex = Extractor()
    cmp_video_object = None
    for search_iter in ex.walk_search("зомбиленд"):
        assert search_iter.search.url == "https://animego.org/anime/zombieland-saga-738"
        assert search_iter.anime.url == "https://animego.org/anime/zombieland-saga-738"
        if "aniboom.one" in search_iter.video.url:
            if not cmp_video_object:
                cmp_video_object = search_iter.video
            assert cmp_video_object == search_iter.video
            sources = search_iter.video.get_source()
            for source in sources:
                assert source.type in ("m3u8", "mpd")
                assert source.quality == 1080
                assert ".cdn-aniboom" in source.url


def test_animego_sibnet():
    ex = Extractor()
    _cmp_video_object = None
    # TODO: maybe need rewrite iterator???
    for search_iter in ex.walk_search("евангелион"):
        # get first season (1995 y)
        if search_iter.search.url != "https://animego.org/anime/evangelion-863":
            return
        assert search_iter.anime.url == "https://animego.org/anime/evangelion-863"
        assert search_iter.search.url == "https://animego.org/anime/evangelion-863"
        if "sibnet" in search_iter.video.url:
            if not _cmp_video_object:
                _cmp_video_object = search_iter.video
            assert _cmp_video_object == search_iter.video
            sources = search_iter.video.get_source()
            for source in sources:
                assert source.type == "mp4"
                assert source.quality == 480
                assert "sibnet" in source.url
