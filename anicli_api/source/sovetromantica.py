import warnings
from typing import List

from parsel import Selector
from scrape_schema import ScField
from scrape_schema.callbacks.parsel import crop_by_xpath_all as cbxa
from scrape_schema.callbacks.parsel import get_attr, get_text, replace_text
from scrape_schema.fields.parsel import ParselXPath, NestedParselList


from anicli_api.base import (
    BaseAnime,
    BaseEpisode,
    BaseExtractor,
    BaseOngoing,
    BaseSearch,
    BaseSource, MainSchema,
)


class Extractor(BaseExtractor):
    BASE_URL = "https://sovetromantica.com"  # BASEURL

    def search(self, query: str) -> List["Search"]:
        response = self.HTTP().get(f"{self.BASE_URL}/anime", params={"query": query})
        return Search.from_crop_rule_list(
            response.text,
            crop_rule=cbxa('//div[@class="anime--block__desu"]'))

    async def a_search(self, query: str) -> List["Search"]:
        # async search entrypoint
        pass

    def ongoing(self) -> List["Ongoing"]:
        # ongoing entrypoint
        response = self.HTTP().get(self.BASE_URL)
        return Ongoing.from_crop_rule_list(
            response.text,
            crop_rule=cbxa('//div[@class="anime--block__desu"]')
        )

    async def a_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.BASE_URL)
            return Ongoing.from_crop_rule_list(
                response.text,
                crop_rule=cbxa('//div[@class="anime--block__desu"]')
            )


class Search(BaseSearch):
    # past xpath to main anime page
    url: ScField[str, ParselXPath('//a', callback=get_attr('href'))]
    name: ScField[str, ParselXPath('//div[@class="anime--block__name"]',
                                   callback=get_text(deep=True, strip=True, sep=" "))]
    # url = property(lambda self: f"https://sovetromantica.com{self._path}")

    def get_anime(self) -> "Anime":
        response = self.HTTP().get(self.url)
        return Anime(response.text)

    async def a_get_anime(self) -> "Anime":
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            return Anime(response.text)

    def __str__(self):
        return self.name


class Ongoing(BaseOngoing):
    # past xpath to main anime page
    _path: ScField[str, ParselXPath('//div[@class="block--full block--shadow"]/a', callback=get_attr('href'))]
    name: ScField[str, ParselXPath('//meta[@itemprop="name"]', callback=get_attr('content'))]
    url = property(lambda self: f"https://sovetromantica.com{self._path}")

    def get_anime(self) -> "Anime":
        response = self.HTTP().get(self.url)
        return Anime(response.text)

    async def a_get_anime(self) -> "Anime":
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            return Anime(response.text)

    def __str__(self):
        return self.name


class Anime(BaseAnime):
    class _Episode(MainSchema):
        name: ScField[str, ParselXPath('//a/div/span')]
        _url_path: ScField[str, ParselXPath('//a', callback=get_attr('href'))]
        image: ScField[str, ParselXPath('//a/img', callback=get_attr('src'))]
        ep_id: ScField[str, ParselXPath('//div', callback=get_attr('id'))]

        @property
        def url(self):
            return f"https://sovetromantica.com{self._url_path}"

    name: ScField[str, ParselXPath('//div[@class="block--full anime-name"]/div[@class="block--container"]')]
    _episodes: ScField[List[_Episode],
                           NestedParselList(
                               _Episode,
                               crop_rule=cbxa("//div[contains(@class, 'episodes-slick_item')]")
                           )]

    def get_episodes(self) -> List["Episode"]:
        if not self._episodes:
            # episodes may not be uploaded. e.g:
            # https://sovetromantica.com/anime/1398-tsundere-akuyaku-reijou-liselotte-to-jikkyou-no-endou-kun-to-kaisetsu-no-kobayashi-san
            warnings.warn("Episodes not available, return empty list", category=RuntimeWarning, stacklevel=3)
            return []
        return [Episode.from_kwargs(**ep.dict()) for ep in self._episodes]

    async def a_get_episodes(self) -> List["Episode"]:
        if not self._episodes:
            # episodes may not be uploaded. e.g:
            # https://sovetromantica.com/anime/1398-tsundere-akuyaku-reijou-liselotte-to-jikkyou-no-endou-kun-to-kaisetsu-no-kobayashi-san
            warnings.warn("Episodes not available, return empty list", category=RuntimeWarning, stacklevel=3)
            return []
        return [Episode.from_kwargs(**ep.dict()) for ep in self._episodes]

    def __str__(self):
        return self.name


class Episode(BaseEpisode):
    name: str
    image: str
    ep_id: str
    url: str

    def get_sources(self) -> List["Source"]:
        response = self.HTTP().get(self.url)
        sel = Selector(response.text)
        video = ParselXPath(
            '//meta[@property="ya:ovs:content_url"]',  callback=get_attr('content')
            ).extract(sel)
        return [Source.from_kwargs(url=video)]

    async def a_get_sources(self) -> List["Source"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            sel = Selector(response.text)
            video = ParselXPath(
                '//meta[@property="ya:ovs:content_url"]', callback=get_attr('content')
            ).extract(sel)
            return [Source.from_kwargs(url=video)]

    def __str__(self):
        return self.name


class Source(BaseSource):
    url: str
    name: str = "SovietRomantica (Subtitles)"

    def __str__(self):
        return self.name


if __name__ == '__main__':
    ex = Extractor()
    s = ex.search('lai')
    ong = ex.ongoing()
    an = s[1].get_anime()
    s[0].get_anime().get_episodes()  # not founded eps
    eps = an.get_episodes()
    sou = eps[0].get_sources()
    vid = sou[0].get_videos()
    print()