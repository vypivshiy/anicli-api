# NOTE: this extractor maybe didn't work in RU
# https://reestr.rublacklist.net/ru/?q=anilibria.tv
from anicli_api.extractors.anilibria import Extractor


def test_cmp_anilibria():
    ex = Extractor()
    cmp_video_obj = None
    for iter_search in ex.search("Зомбиленд")[0]:
        if not cmp_video_obj:
            cmp_video_obj = iter_search.video
        assert cmp_video_obj == iter_search.video
        sources = iter_search.video.get_source()
        for source in sources:
            assert source.type == "m3u8"
            assert "libria.fun" in source.url
