"""Animego extractor
WARNING! THIS EXTRACTOR WORKS ONLY WHICH MOBILE USERAGENT!!!"""
from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, Generator, Protocol, Union

from anicli_api.base import *


class SearchIterData(Protocol):
    search: SearchResult
    anime: AnimeInfo
    episode: Episode
    video: Video


class OngoingIterData(Protocol):
    search: Ongoing
    anime: AnimeInfo
    episode: Episode
    video: Video


class Extractor(BaseAnimeExtractor):
    BASE_URL = "https://animego.org/"

    def async_walk_search(self, query: str) -> AsyncGenerator[SearchIterData, None]:
        return super().async_walk_search(query)

    def async_walk_ongoing(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().async_walk_ongoing()

    def walk_search(self, query: str) -> Generator[SearchIterData, None, None]:
        return super().walk_search(query)

    def walk_ongoing(self) -> Generator[OngoingIterData, None, None]:
        return super().walk_ongoing()

    def search(self, query: str) -> List["SearchResult"]:
        response = self.HTTP().get(f"{self.BASE_URL}search/anime", params={"q": query})
        result = self._ReFieldListDict(
            r'data-original="(?P<thumbnail>https://animego\.org/media/[^>]+\.\w{2,4})".*'
            r'<a href="(?P<url>https://animego\.org/anime/[^>]+)" '
            r'title="(?P<name>[^>]+)".*'
            r'href="https://animego\.org/anime/type/[^>]+>(?P<type>[^>]+)<[^>]+.*'
            r'href="https://animego\.org/anime/season/(?P<year>\d+)',
            name="info",
            after_exec_type={"year": lambda i: int(i)},
        ).parse_values(response.text)
        # {thumbnail:str, url: str, name: str, type: str, year: int}
        return [SearchResult(**data) for data in result]

    async def async_search(self, query: str) -> List["SearchResult"]:
        # TODO refactoring duplicate code
        async with self.HTTP_ASYNC() as session:
            response = await session.get(f"{self.BASE_URL}search/anime", params={"q": query})
            result = self._ReFieldListDict(
                r'data-original="(?P<thumbnail>https://animego\.org/media/[^>]+\.\w{2,4})".*'
                r'<a href="(?P<url>https://animego\.org/anime/[^>]+)" '
                r'title="(?P<name>[^>]+)".*'
                r'href="https://animego\.org/anime/type/[^>]+>(?P<type>[^>]+)<[^>]+.*'
                r'href="https://animego\.org/anime/season/(?P<year>\d+)',
                name="info",
                after_exec_type={"year": lambda i: int(i)},
            ).parse_values(response.text)
        return [SearchResult(**data) for data in result]

    async def async_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as session:
            response = await session.get(f"{self.BASE_URL}search/anime")
            result = self._ReFieldListDict(
                r'onclick="location\.href=\'(?P<url>[^>]+)\'.*?url\((?P<thumbnail>[^>]+)\);.*?'
                r'<span class="[^>]+"><span class="[^>]+">(?P<name>[^>]+)</span>.*?'
                r'<div class="[^>]+"><div class="[^>]+">(?P<num>[^>]+)'
                r'</div><div class="[^>]+">\((?P<dub>[^>]+)\)',
                name="info",
                after_exec_type={
                    "url": lambda s: f"https://animego.org{s}",
                    "num": lambda s: int(s.split()[0]),
                },
            ).parse_values(response.text)
            # {url: str, thumbnail: str, name: str, num: int, dub: str}
            # return [Ongoing(**data) for data in result]
            return self._ongoing_sort(result)

    @staticmethod
    def _ongoing_sort(raw_parsed_data: List[Dict]) -> List["Ongoing"]:
        # remove url duplicates
        seen: Dict[str, Dict] = {}
        for ong in raw_parsed_data:
            if not seen.get(ong["url"]):
                seen[ong["url"]] = ong
            else:
                old_ong = seen[ong["url"]]
                if seen[ong["url"]]["num"] < ong["num"]:
                    # set max available episode num
                    seen[ong["url"]]["num"] = ong["num"]
                old_ong["dub"] = f'{old_ong["dub"]}, {ong["dub"]}'
        return [Ongoing(**kw) for kw in seen.values()]

    def ongoing(self) -> List["Ongoing"]:
        response = self.HTTP().get(self.BASE_URL)
        result = self._ReFieldListDict(
            r'onclick="location\.href=\'(?P<url>[^>]+)\'.*?url\((?P<thumbnail>[^>]+)\);.*?'
            r'<span class="[^>]+"><span class="[^>]+">(?P<name>[^>]+)</span>.*?'
            r'<div class="[^>]+"><div class="[^>]+">(?P<num>[^>]+)'
            r'</div><div class="[^>]+">\((?P<dub>[^>]+)\)',
            name="info",
            after_exec_type={
                "url": lambda s: f"https://animego.org{s}",
                "num": lambda s: int(s.split()[0]),
            },
        ).parse_values(response.text)
        # {url: str, thumbnail: str, name: str, num: int, dub: str}
        # return [Ongoing(**data) for data in result]
        return self._ongoing_sort(result)


class AnimeParser(BaseModel):
    """avoid duplicate code"""

    url: str

    @classmethod
    def _soup_extract_table(cls, soup) -> Dict[str, Union[str, List[str]]]:
        meta: Dict[str, Union[List[str], str]] = {}
        # get from table metadata
        for el in soup.find("dl", attrs={"class": "row"}).find_all("dt"):
            key = el.get_text(strip=True)
            value = el.find_next("dd").get_text(strip=True)
            meta[key] = value
        return meta

    def _extract_data(self, response: str) -> dict:
        soup = self._soup(response)
        meta = self._soup_extract_table(soup)

        meta["name"] = soup.find("div", attrs={"class": "anime-title"}).find_next("h1").get_text()
        meta["alt_names"] = [
            t.get_text(strip=True)
            for t in soup.find("div", attrs={"class": "synonyms"}).find_all("li")
        ]
        try:
            meta["rating"] = (
                soup.find("span", class_="rating-value").get_text(strip=True).replace(",", ".")
            )
        except Exception:
            meta["rating"] = "0"
        meta["description"] = soup.find("div", attrs={"data-readmore": "content"}).get_text(
            strip=True
        )
        meta["genres"] = meta.get("genres").split(",") if meta.get("genres") else []  # type: ignore
        meta["id"] = self.url.split("-")[-1]
        meta["screenshots"] = self._ReFieldList(
            r'<a class="screenshots-item[^>]+" href="([^>]+)" data-ajax',
            name="screenshots",
            after_exec_type=lambda s: f"https://animego.org{s}",
        ).parse_values(response)
        meta["thumbnails"] = self._ReFieldList(
            r'class="img-fluid" src="([^>]+)"', name="a"
        ).parse_values(response)
        meta["dubs"] = meta.get("dubs").split(",") if meta.get("dubs") else []  # type: ignore
        meta["url"] = self.url
        return meta

    def get_anime(self) -> "AnimeInfo":
        response = self._HTTP().get(self.url).text
        meta = self._extract_data(response)
        return AnimeInfo(**meta)

    async def a_get_anime(self) -> "AnimeInfo":
        async with self._HTTP_ASYNC() as session:
            response = (await session.get(self.url)).text
            meta = self._extract_data(response)
            return AnimeInfo(**meta)


class SearchResult(AnimeParser, BaseSearchResult):
    name: str
    type: str
    # meta
    year: int
    thumbnail: str

    def __iter__(self) -> Generator[SearchIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[SearchIterData, None]:
        return super().__aiter__()

    def __str__(self):
        return f"{self.name} {self.type} {self.year}"


class Ongoing(AnimeParser, BaseOngoing):
    name: str
    num: str

    # meta
    thumbnail: str
    dub: str

    def __iter__(self) -> Generator[OngoingIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().__aiter__()

    def __str__(self):
        return f"{self.name} {self.num} {self.dub}"


class AnimeInfo(BaseAnimeInfo):
    id: str
    url: str

    # meta
    name: str
    alt_names: list[str]
    rating: float
    description: str
    genres: list[str]
    screenshots: list[str]
    thumbnails: list[str]

    async def a_get_episodes(self) -> List["Episode"]:
        # TODO
        async with self._HTTP_ASYNC() as session:
            response = (
                await session.get(
                    f"https://animego.org/anime/{self.id}/player", params={"_allow": "true"}
                )
            ).json()["content"]
            episodes = self._ReFieldListDict(
                r'''data-episode="(?P<num>\d+)"
        \s*data-id="(?P<id>\d+)"
        \s*data-episode-type="(?P<type>.*?)"
        \s*data-episode-title="(?P<name>.*?)"
        \s*data-episode-released="(?P<released>.*?)"
        \s*data-episode-description="(?P<description>.*?)"''',
                name="episodes",
                after_exec_type={"num": int, "id": int, "type": int},
            ).parse_values(response)
        return [Episode(url=self.url, **ep) for ep in episodes]

    def get_episodes(self) -> List["Episode"]:
        response = (
            self._HTTP()
            .get(f"https://animego.org/anime/{self.id}/player", params={"_allow": "true"})
            .json()["content"]
        )
        episodes = self._ReFieldListDict(
            r'''data-episode="(?P<num>\d+)"
        \s*data-id="(?P<id>\d+)"
        \s*data-episode-type="(?P<type>.*?)"
        \s*data-episode-title="(?P<name>.*?)"
        \s*data-episode-released="(?P<released>.*?)"
        \s*data-episode-description="(?P<description>.*?)"''',
            name="episodes",
            after_exec_type={"num": int, "id": int, "type": int},
        ).parse_values(response)
        return [Episode(url=self.url, **ep) for ep in episodes]

    def __str__(self):
        return f"{self.name} {self.rating}\n{self.genres}\n{self.description}"


class Episode(BaseEpisode):
    id: int
    num: int
    # meta
    type: int
    name: str
    released: str
    description: str
    url: str

    def _extract_metadata(self, response: str) -> List[dict]:
        dubs = self._ReFieldListDict(
            r'data-dubbing="(?P<dub_id>\d+)"><span [^>]+>\s*(?P<dub>[\w\s\-]+)\n',
            name="dubs",
            after_exec_type={"id": int},
        ).parse_values(response)

        videos = self._ReFieldListDict(
            r'player="(?P<url>//[\w/\.\?&;=]+)"'
            r"[^>]+data-[\w\-]"  # aniboom - data-provide-dubbing kodik  - data-provider strings
            r'+="(?P<dub_id>\d+)"><span[^>]+>(?P<name>[^>]+)<',
            name="videos",
            after_exec_type={"id": int, "url": lambda u: f"https:{u}"},
        ).parse_values(response)
        result: List[dict] = []
        for video in videos:
            result.extend({**dub, **video} for dub in dubs if video["dub_id"] == dub["dub_id"])
        return result

    async def a_get_videos(self) -> List["Video"]:
        # TODO
        async with self._HTTP_ASYNC() as session:
            resp = (
                await session.get(
                    "https://animego.org/anime/series",
                    params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.id},
                )
            ).json()["content"]
            result = self._extract_metadata(resp)
            return [Video(**vid) for vid in result]

    def get_videos(self) -> List["Video"]:
        resp = (
            self._HTTP()
            .get(
                "https://animego.org/anime/series",
                params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.id},
            )
            .json()["content"]
        )

        result = self._extract_metadata(resp)
        return [Video(**vid) for vid in result]

    def __str__(self):
        return f"{self.num} {self.name} {self.description}"


class Video(BaseVideo):
    __CMP_KEYS__ = ("dub",)
    dub_id: int
    dub: str
    name: str


class TestCollections(BaseTestCollections):
    def test_search(self):
        resp = Extractor().search("lain")
        assert resp[0].dict() == {
            "thumbnail": "https://animego.org/media/cache/thumbs_300x420/upload/anime/images/5d1b809ecb40b061887856.jpg",
            "url": "https://animego.org/anime/eksperimenty-leyn-1114",
            "name": "Эксперименты Лэйн",
            "type": "ТВ Сериал",
            "year": 1998,
        }

    def test_ongoing(self):
        ongs = Extractor().ongoing()
        assert len(ongs) > 1

    def test_extract_metadata(self):
        for meta in Extractor().search("lain")[0]:
            assert meta.search.url == "https://animego.org/anime/eksperimenty-leyn-1114"
            assert meta.anime.url == "https://animego.org/anime/eksperimenty-leyn-1114"
            assert meta.episode.num == 1

    def test_extract_video(self):
        for meta in Extractor().search("lain")[0]:
            assert "kodik" in meta.video.url
            assert meta.video.get_source()[0].url.endswith(".m3u8")
