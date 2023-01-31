from anicli_api.extractors.animania import Extractor


def test_animania_kodik():
    ex = Extractor()
    cmp_video_object = None
    for meta in ex.search("serial experiments lain")[0]:
        if not cmp_video_object:
            cmp_video_object = meta.video
        assert cmp_video_object == meta.video
        assert "kodik" in meta.video.url
        source = meta.video.get_source()[-1]
        assert source.type == "m3u8"
        assert source.quality == 720
