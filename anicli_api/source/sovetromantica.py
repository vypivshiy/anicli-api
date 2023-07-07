import warnings
from typing import List

from parsel import Selector
from scrape_schema import Sc, sc_param, Parsel, Nested

from anicli_api.base import (
    BaseAnime,
    BaseEpisode,
    BaseExtractor,
    BaseOngoing,
    BaseSearch,
    BaseSource,
    MainSchema,
)


class Extractor(BaseExtractor):
    BASE_URL = "https://sovetromantica.com"  # BASEURL

    def search(self, query: str) -> List["Search"]:
        response = self.HTTP().get(f"{self.BASE_URL}/anime", params={"query": query})
        chunks = Parsel().xpath('//div[@class="anime--block__desu"]').getall().sc_parse(response.text)
        return [Search(ch) for ch in chunks]

    async def a_search(self, query: str) -> List["Search"]:
        # async search entrypoint
        async with self.HTTP_ASYNC() as client:
            response = await client.get(f"{self.BASE_URL}/anime", params={"query": query})
            chunks = Parsel().xpath('//div[@class="anime--block__desu"]').getall().sc_parse(response.text)
            return [Search(ch) for ch in chunks]

    def ongoing(self) -> List["Ongoing"]:
        # ongoing entrypoint
        response = self.HTTP().get(self.BASE_URL)
        chunks = Parsel().xpath('//div[@class="anime--block__desu"]').getall().sc_parse(response.text)
        return [Ongoing(ch) for ch in chunks]

    async def a_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.BASE_URL)
            chunks = Parsel().xpath('//div[@class="anime--block__desu"]').getall().sc_parse(response.text)
            return [Ongoing(ch) for ch in chunks]


class Search(BaseSearch):
    # past xpath to main anime page
    url: Sc[str, Parsel().xpath("//a/@href").get()]
    name: Sc[str, Parsel().xpath('//div[@class="anime--block__name"]/text()').get()]
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
    _path: Sc[str, Parsel().xpath('//div[@class="block--full block--shadow"]/a/@href').get()]
    name: Sc[str, Parsel().xpath('//meta[@itemprop="name"]/@content').get()]
    url: str = sc_param(lambda self: f"https://sovetromantica.com{self._path}")

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
        name: Sc[str, Parsel().xpath("//a/div/span/text()").get()]
        _url_path: Sc[str, Parsel().xpath("//a/@href").get()]
        image: Sc[str, Parsel().xpath("//a/img/@src").get()]
        ep_id: Sc[str, Parsel().xpath("//div/@id").get()]

        @sc_param
        def url(self):
            return f"https://sovetromantica.com{self._url_path}"

    name: Sc[str, Parsel().xpath('//div[@class="block--full anime-name"]/div[@class="block--container"]/text()').get()]
    _episodes: Sc[List[_Episode], Nested(Parsel().xpath("//div[contains(@class, 'episodes-slick_item')]").getall())]

    def get_episodes(self) -> List["Episode"]:
        if not self._episodes:
            # episodes may not be uploaded. e.g:
            # https://sovetromantica.com/anime/1398-tsundere-akuyaku-reijou-liselotte-to-jikkyou-no-endou-kun-to-kaisetsu-no-kobayashi-san
            warnings.warn(
                "Episodes not available, return empty list", category=RuntimeWarning, stacklevel=3
            )
            return []
        return [Episode.from_kwargs(**ep.dict()) for ep in self._episodes]

    async def a_get_episodes(self) -> List["Episode"]:
        if not self._episodes:
            # episodes may not be uploaded. e.g:
            # https://sovetromantica.com/anime/1398-tsundere-akuyaku-reijou-liselotte-to-jikkyou-no-endou-kun-to-kaisetsu-no-kobayashi-san
            warnings.warn(
                "Episodes not available, return empty list", category=RuntimeWarning, stacklevel=3
            )
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
        video = Parsel().xpath(
            '//meta[@property="ya:ovs:content_url"]/@content').get().sc_parse(response.text)
        return [Source.from_kwargs(url=video)]

    async def a_get_sources(self) -> List["Source"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            video = Parsel().xpath(
                '//meta[@property="ya:ovs:content_url"]/@content').get().sc_parse(response.text)
            return [Source.from_kwargs(url=video)]

    def dict(self):
        return {"name": self.name, "image": self.image, "ep_id": self.ep_id, "url": self.url}

    def __str__(self):
        return self.name


class Source(BaseSource):
    url: str
    name: str = "SovietRomantica (Subtitles)"

    def dict(self):
        return {"url": self.url, "name": self.name}

    def __str__(self):
        return self.name


if __name__ == "__main__":
    ex = Extractor()
    s = ex.search("lai")
    ong = ex.ongoing()
    an = s[1].get_anime()
    s[0].get_anime().get_episodes()  # not founded eps
    eps = an.get_episodes()
    sou = eps[0].get_sources()
    vid = sou[0].get_videos()
    print(vid)
