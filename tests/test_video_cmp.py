import pytest

from anicli_api.player.base import Video


@pytest.mark.parametrize(
    'video_1, video_2, result',
    [
        (Video('mp4', 144, 'https://example.com'), Video('mp4', 144, 'https://example.com'), True),
        (Video('mp4', 144, 'https://a.example.com'), Video('mp4', 144, 'https://example.com'), True),
        (Video('mp4', 144, 'https://a.b.c.d.x.y.z.example.com/aaa'), Video('mp4', 144, 'https://example.com/c'), True),

        (Video('mp4', 240, 'https://example.com'), Video('mp4', 144, 'https://example.com'), False),
        (Video('mp4', 144, 'https://myexample.org'), Video('mp4', 144, 'https://example.com'), False),
        (Video('m3u8', 144, 'https://example.com'), Video('mp4', 144, 'https://example.com'), False),

    ]
)
def test_video_cmp(video_1, video_2, result):
    assert (video_1 == video_2) == result
