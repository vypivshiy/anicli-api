import pytest

from anicli_api.base import BaseSearch, BaseOngoing, BaseAnime, BaseEpisode, BaseSource


@pytest.mark.parametrize(
    'item_1, item_2, result', [
        (BaseSearch(title='1', url='_', thumbnail='_'), BaseSearch(title='1', url='_', thumbnail='_'), True),
        (BaseSearch(title='2', url='_', thumbnail='_'), BaseSearch(title='1', url='_', thumbnail='_'), False),

        (BaseOngoing(title='1', url='_', thumbnail='_'), BaseOngoing(title='1', url='_', thumbnail='_'), True),
        (BaseOngoing(title='2', url='_', thumbnail='_'), BaseOngoing(title='1', url='_', thumbnail='_'), False),

        (BaseAnime(title='2', description='_', thumbnail='_'), BaseAnime(title='1', description='_', thumbnail='_'), False),
        (BaseEpisode(title='1', num='_'), BaseEpisode(title='2', num='_'), False),
        (BaseSource(title='1', url='_'), BaseSource(title='2', url='_'), False),
    ])
def test_cmp_items(item_1, item_2, result):
    assert (item_1 == item_2) == result
