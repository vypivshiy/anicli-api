import warnings
from typing import List

from scrape_schema import Nested, Parsel, Sc, sc_param

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource, MainSchema


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
        response = self.HTTP().get(f"{self.BASE_URL}/anime")
        chunks = Parsel().xpath('//div[@class="anime--block__desu"]').getall().sc_parse(response.text)
        return [Ongoing(ch) for ch in chunks]

    async def a_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.BASE_URL)
            chunks = Parsel().xpath('//div[@class="anime--block__desu"]').getall().sc_parse(response.text)
            return [Ongoing(ch) for ch in chunks]


class Search(BaseSearch):
    url: Sc[str, Parsel().xpath("//a/@href").get()]
    title: Sc[str, Parsel().xpath('//div[@class="anime--block__name"]/text()').get()]
    thumbnail: Sc[str, Parsel().xpath('//*[@class="anime--poster lazy loaded"]/@src').get()]
    # url = property(lambda self: f"https://sovetromantica.com{self._path}")

    def get_anime(self) -> "Anime":
        response = self.HTTP().get(self.url)
        return Anime(response.text)

    async def a_get_anime(self) -> "Anime":
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            return Anime(response.text)

    def __str__(self):
        return self.title


class Ongoing(BaseOngoing):
    # past xpath to main anime page
    url: Sc[str, Parsel().xpath("//a/@href").get()]
    title: Sc[str, Parsel().xpath('//div[@class="anime--block__name"]/text()').get()]
    thumbnail: Sc[str, Parsel().xpath('//*[@class="anime--poster lazy loaded"]/@src').get()]

    def get_anime(self) -> "Anime":
        response = self.HTTP().get(self.url)
        return Anime(response.text)

    async def a_get_anime(self) -> "Anime":
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            return Anime(response.text)

    def __str__(self):
        return self.title


class Anime(BaseAnime):
    class _Episode(MainSchema):
        title: Sc[str, Parsel().xpath("//a/div/span/text()").get()]
        _url_path: Sc[str, Parsel().xpath("//a/@href").get()]
        image: Sc[str, Parsel().xpath("//a/img/@src").get()]
        ep_id: Sc[str, Parsel().xpath("//div/@id").get()]

        @sc_param
        def num(self) -> int:
            return int(self.title.split("#")[-1])

        @sc_param
        def url(self):
            return f"https://sovetromantica.com{self._url_path}"

    _titles: Sc[
        str,
        Parsel().xpath('//div[@class="block--full anime-name"]/div[@class="block--container"]/text()').get(),
    ]

    _episodes: Sc[
        List[_Episode],
        Nested(Parsel().xpath("//div[contains(@class, 'episodes-slick_item')]").getall()),
    ]

    @sc_param
    def title(self):
        return self._titles.split(" / ")[0]

    @sc_param
    def alt_titles(self):
        return [self._titles.split(" / ")[-1]]

    thumbnail: Sc[str, Parsel().xpath('//*[@id="poster"]/@src').get()]
    description = None
    genres: Sc[List[str], Parsel().xpath('//div[@class="animeTagInfo"]/a/text()').getall()]
    episodes_available = None
    episodes_total = None
    aired = None

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
        return self.title


class Episode(BaseEpisode):
    title: str
    num: int
    image: str
    ep_id: str
    url: str

    def dict(self):
        return {"title": self.title, "num": self.num}

    def get_sources(self) -> List["Source"]:
        response = self.HTTP().get(self.url)
        video = Parsel().xpath('//meta[@property="ya:ovs:content_url"]/@content').get().sc_parse(response.text)
        return [Source.from_kwargs(url=video)]

    async def a_get_sources(self) -> List["Source"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            video = Parsel().xpath('//meta[@property="ya:ovs:content_url"]/@content').get().sc_parse(response.text)
            return [Source.from_kwargs(url=video)]

    def __str__(self):
        return f"{self.num} {self.title}"


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
