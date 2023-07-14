from typing import Dict, List, TypedDict
from urllib.parse import urlsplit

from scrape_schema import Parsel, Sc, sc_param

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

_SourceDict = TypedDict("_SourceDict", {"player_id": str, "url": str, "name": str})


class Extractor(BaseExtractor):
    BASE_URL = "https://animejoy.ru"

    def search(self, query: str) -> List["Search"]:
        # search entrypoint
        response = (
            self.HTTP()
            .post(
                self.BASE_URL,
                data={"story": query, "do": "search", "subaction": "search"},
            )
            .text
        )
        chunks = (
            Parsel()
            .xpath('//*[@id="dle-content"]/article[@class="block story shortstory"]')
            .getall()
            .sc_parse(response)
        )
        return [Search(ch) for ch in chunks]

    async def a_search(self, query: str) -> List["Search"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.post(self.BASE_URL, data={"story": query, "do": "search", "subaction": "search"})
            chunks = (
                Parsel()
                .xpath('//*[@id="dle-content"]/article[@class="block story shortstory"]')
                .getall()
                .sc_parse(response)
            )
            return [Search(ch) for ch in chunks]

    def ongoing(self) -> List["Ongoing"]:
        # ongoing entrypoint
        response = self.HTTP().get(self.BASE_URL).text
        chunks = Parsel().xpath('//div[@id="dle-content"]/article').getall().sc_parse(response)
        return [Ongoing(ch) for ch in chunks]

    async def a_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.BASE_URL)
            chunks = Parsel().xpath('//div[@id="dle-content"]/article').getall().sc_parse(response)
            return [Ongoing(ch) for ch in chunks]


class Search(BaseSearch):
    url: Sc[str, Parsel().xpath('//div[@class="titleup"]/h2/a/@href').get()]
    title: Sc[str, Parsel().xpath('//div[@class="titleup"]/h2/a/text()').get()]
    alt_name: Sc[
        str,
        Parsel().xpath('//div[@class="blkdesc"]/p/span[@itemprop="alternativeHeadline"]/text()').get(),
    ]
    _thumbnail_path: Sc[str, Parsel().xpath('//div[@class="text"]/picture/img').get()]
    _metadata: Sc[List[str], Parsel().xpath('//div[@class="blkdesc"]/p[@class="zerop"]/text()').getall()]
    thumbnail = sc_param(lambda self: f"https://animejoy.ru{self._thumbnail_path}")

    def get_anime(self) -> "Anime":
        response = self.HTTP().get(self.url).text
        return Anime(response)

    async def a_get_anime(self) -> "Anime":
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            return Anime(response.text)

    def __str__(self):
        return f"{self.title} ({self.alt_name})"


class Ongoing(BaseOngoing):
    url: Sc[str, Parsel().xpath('//div[@class="titleup"]/h2/a/@href').get()]
    title: Sc[str, Parsel().xpath('//div[@class="titleup"]/h2/a/text()').get()]
    alt_name: Sc[
        str,
        Parsel().xpath('//div[@class="blkdesc"]/p/span[@itemprop="alternativeHeadline"]/text()').get(),
    ]
    _thumbnail_path: Sc[str, Parsel().xpath('//div[@class="text"]/picture/img/@src').get()]
    _metadata: Sc[List[str], Parsel().xpath('//div[@class="blkdesc"]/p[@class="zerop"]/text()').getall()]
    thumbnail = sc_param(lambda self: f"https://animejoy.ru{self._thumbnail_path}")

    def get_anime(self) -> "Anime":
        response = self.HTTP().get(self.url)
        return Anime(response)

    async def a_get_anime(self) -> "Anime":
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            return Anime(response)

    def __str__(self):
        return f"{self.title} ({self.alt_name})"


class Anime(BaseAnime):
    _thumbnail_path: Sc[str, Parsel().css(".fr-fil").xpath("@src").get()]
    _released_episodes: Sc[List[int], Parsel().css("li > span::text")[-1].re(r"(\d+)")]
    _alt_titles: Sc[str, Parsel().xpath('//h2[@class="romanji"]/text()').get()]

    title: Sc[str, Parsel().xpath('//h1[@class="h2 ntitle"]/text()').get()]

    @sc_param
    def alt_titles(self):
        return [self._alt_titles]

    thumbnail = sc_param(lambda self: f"https://animejoy.ru{self._thumbnail_path}")
    description: Sc[str, Parsel().xpath('//div[@class="pcdescrf"]/p/text()').get()]
    genres: Sc[List[str], Parsel().css(".zerop:nth-child(2) > span > a::text").getall()]

    @sc_param
    def episodes_total(self) -> int:
        return self._released_episodes[-1]

    @sc_param
    def episodes_available(self) -> int:
        return self._released_episodes[0]

    aired: Sc[
        str,
        Parsel().xpath('//*[@id="dle-content"]/article/div[1]/div[2]/div[2]/p[5]/text()').get(),
    ]

    url: Sc[str, Parsel().xpath('//meta[@property="og:url"]/@content').get()]
    news_id = sc_param(lambda self: self.url.split("/")[-1].split("-")[0])

    def __str__(self):
        return f"{self.title} {self.alt_titles}"

    def _extract_episode_meta(self, response: str) -> List["Episode"]:
        # get player ids and names for better output
        sel = self.__selector__.__class__(response)
        players_ids = sel.xpath('//div[@class="playlists-lists"]/div[@class="playlists-items"]/ul/li/@data-id').getall()

        players_names = sel.xpath('//div[@class="playlists-lists"]/div[@class="playlists-items"]/ul/li/text()').getall()
        players_table = dict(zip(players_ids, players_names))

        # extract episodes names, video urls, and player ids
        series_names = sel.xpath('//div[@class="playlists-videos"]/div[@class="playlists-items"]/ul/li/text()').getall()
        series_urls = sel.xpath(
            '//div[@class="playlists-videos"]/div[@class="playlists-items"]/ul/li/@data-file'
        ).getall()
        series_player_id = sel.xpath(
            '//div[@class="playlists-videos"]/div[@class="playlists-items"]/ul/li/@data-id'
        ).getall()

        episodes_dict: Dict[str, List[Dict[str, str]]] = {}
        for name, url, player_id in zip(series_names, series_urls, series_player_id):
            if not episodes_dict.get(name):
                episodes_dict[name] = []
            if url.startswith("//"):
                url = f"https:{url}"

            episodes_dict[name].append(
                {
                    "url": url,
                    "name": players_table.get(player_id, "unknown"),
                    "player_id": player_id,
                }
            )
        return [Episode.from_kwargs(name=name, _video_meta=video_meta) for name, video_meta in episodes_dict.items()]

    def get_episodes(self) -> List["Episode"]:
        response = (
            self.HTTP()
            .get(
                "https://animejoy.ru/engine/ajax/playlists.php",
                params={"news_id": self.news_id, "xfield": "playlist"},
            )
            .json()["response"]
        )
        return self._extract_episode_meta(response)

    async def a_get_episodes(self) -> List["Episode"]:
        async with self.HTTP_ASYNC() as client:
            response = (
                await client.get(
                    "https://animejoy.ru/engine/ajax/playlists.php",
                    params={"news_id": self.news_id, "xfield": "playlist"},
                )
            ).json()["response"]
            # crop to parts html players, series tags for better view outup
            return self._extract_episode_meta(response)


class Episode(BaseEpisode):
    _video_meta: List[_SourceDict]
    name: str

    def __str__(self):
        return self.name

    @sc_param
    def num(self) -> int:
        return int(self.name.split(" ")[0])

    def dict(self):
        return {"name": self.name, "meta": self._video_meta}

    def get_sources(self) -> List["Source"]:
        return [
            Source.from_kwargs(url=meta["url"], name=meta["name"], player_id=meta["player_id"])
            for meta in self._video_meta
        ]

    async def a_get_sources(self) -> List["Source"]:
        return self.get_sources()


class Source(BaseSource):
    url: str
    name: str
    player_id: str

    def dict(self):
        return {"url": self.url, "name": self.name, "player_id": self.player_id}

    def __str__(self):
        return f"{urlsplit(self.url).netloc} ({self.name})"


if __name__ == "__main__":
    ex = Extractor()
    res = ex.search("lai")
    an = res[0].get_anime()
    eps = an.get_episodes()
    vids = eps[0].get_sources()
    print(*[v.dict() for v in vids], sep="\n")
    print(vids[1].get_videos())
