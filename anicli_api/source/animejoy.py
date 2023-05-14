from typing import Dict, List, TypedDict
from urllib.parse import urlsplit

from parsel import Selector
from scrape_schema import ScField
from scrape_schema.callbacks.parsel import crop_by_xpath_all as cbxa
from scrape_schema.callbacks.parsel import get_attr, get_text
from scrape_schema.fields.parsel import ParselXPath, ParselXPathList

from anicli_api.base import (
    BaseAnime,
    BaseEpisode,
    BaseExtractor,
    BaseOngoing,
    BaseSearch,
    BaseSource,
)

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
        return Search.from_crop_rule_list(
            response,
            crop_rule=cbxa('//*[@id="dle-content"]/article[@class="block story shortstory"]'),
        )

    async def a_search(self, query: str) -> List["Search"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.post(
                self.BASE_URL, data={"story": query, "do": "search", "subaction": "search"}
            )
            return Search.from_crop_rule_list(
                response,
                crop_rule=cbxa('//*[@id="dle-content"]/article[@class="block story shortstory"]'),
            )

    def ongoing(self) -> List["Ongoing"]:
        # ongoing entrypoint
        response = self.HTTP().get(self.BASE_URL).text
        return Ongoing.from_crop_rule_list(
            response, crop_rule=cbxa('//div[@id="dle-content"]/article')
        )

    async def a_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.BASE_URL)
            return Ongoing.from_crop_rule_list(
                response.text, crop_rule=cbxa('//div[@id="dle-content"]/article')
            )


class Search(BaseSearch):
    url: ScField[str, ParselXPath('//div[@class="titleup"]/h2/a', callback=get_attr("href"))]
    title: ScField[str, ParselXPath('//div[@class="titleup"]/h2/a')]
    alt_name: ScField[
        str, ParselXPath('//div[@class="blkdesc"]/p/span[@itemprop="alternativeHeadline"]')
    ]
    _thumbnail_path: ScField[str, ParselXPath('//div[@class="text"]/picture/img')]
    _metadata: ScField[
        List[str],
        ParselXPathList(
            '//div[@class="blkdesc"]/p[@class="zerop"]', callback=get_text(strip=True, deep=True)
        ),
    ]
    thumbnail = property(lambda self: f"https://animejoy.ru{self._thumbnail_path}")

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
    url: ScField[str, ParselXPath('//div[@class="titleup"]/h2/a', callback=get_attr("href"))]
    title: ScField[str, ParselXPath('//div[@class="titleup"]/h2/a')]
    alt_name: ScField[
        str, ParselXPath('//div[@class="blkdesc"]/p/span[@itemprop="alternativeHeadline"]')
    ]
    _thumbnail_path: ScField[str, ParselXPath('//div[@class="text"]/picture/img', callback=get_attr('src'))]
    _metadata: ScField[
        List[str],
        ParselXPathList(
            '//div[@class="blkdesc"]/p[@class="zerop"]', callback=get_text(strip=True, deep=True)
        ),
    ]
    thumbnail = property(lambda self: f"https://animejoy.ru{self._thumbnail_path}")

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
    title: ScField[str, ParselXPath('//h1[@class="h2 ntitle"]')]
    alt_name: ScField[str, ParselXPath('//h2[@class="romanji"]')]
    _thumbnail_path: ScField[str, ParselXPath('//div[@class="text"]/picture/img', callback=get_attr('src'))]
    thumbnail = property(lambda self: f"https://animejoy.ru{self._thumbnail_path}")
    _metadata: ScField[List[str], ParselXPathList('//div[@class="blkdesc"]/p[@class="zerop"]')]
    description: ScField[
        str, ParselXPath('//div[@class="pcdescrf"]', callback=get_text(deep=True))
    ]
    screenshots: ScField[
        List[str],
        ParselXPathList('//div[@class="photo-row clearfix"]/a', callback=get_attr("href")),
    ]
    url: ScField[str, ParselXPath('//meta[@property="og:url"]', callback=get_attr("content"))]
    news_id = property(lambda self: self.url.split("/")[-1].split("-")[0])

    def __str__(self):
        return f"{self.title} ({self.alt_name})"

    def _extract_episode_meta(self, response: str) -> List["Episode"]:
        sel = Selector(response)
        # get player ids and names for better output
        players_ids = sel.xpath(
            '//div[@class="playlists-lists"]/div[@class="playlists-items"]/ul/li/@data-id'
        ).getall()
        players_names = sel.xpath(
            '//div[@class="playlists-lists"]/div[@class="playlists-items"]/ul/li/text()'
        ).getall()
        players_table = dict(zip(players_ids, players_names))

        # extract episodes names, video urls, and player ids
        series_names = sel.xpath(
            '//div[@class="playlists-videos"]/div[@class="playlists-items"]/ul/li/text()'
        ).getall()
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
        return [
            Episode.from_kwargs(name=name, _video_meta=video_meta)
            for name, video_meta in episodes_dict.items()
        ]

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
            return self._extract_episode_meta(response)


class Episode(BaseEpisode):
    _video_meta: List[_SourceDict]
    name: str

    def __str__(self):
        return self.name

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

    def __str__(self):
        return f"{urlsplit(self.url).netloc} ({self.name})"


if __name__ == "__main__":
    ex = Extractor()
    res = ex.search("lai")
    an = res[0].get_anime()
    eps = an.get_episodes()
    vids = eps[0].get_sources()
    print(*[v.raw_dict() for v in vids], sep="\n")
    print(vids[1].get_videos())
