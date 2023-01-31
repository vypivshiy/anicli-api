from anicli_api.extractors.animevost import Extractor


def test_animevost_cmp():
    ex = Extractor()
    cmp_video_object = None
    for meta in ex.search("serial experiments lain")[0]:
        if not cmp_video_object:
            cmp_video_object = meta.video
        assert cmp_video_object == meta.video
        for source in meta.video.get_source():
            assert source.type == "mp4"