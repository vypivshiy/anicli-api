"""Animania Extractor"""
from __future__ import annotations

from typing import AsyncGenerator, Dict, Generator, Protocol

from anicli_api.base import *

__all__ = (
    "Extractor",
    "SearchResult",
    "Ongoing",
    "AnimeInfo",
    "Episode",
    "Video",
    "TestCollections",
)


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
    BASE_URL = "https://animania.online"

    def async_walk_search(self, query: str) -> AsyncGenerator[SearchIterData, None]:
        return super().async_walk_search(query)

    def walk_search(self, query: str) -> Generator[SearchIterData, None, None]:
        return super().walk_search(query)

    def async_walk_ongoing(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().async_walk_ongoing()

    def walk_ongoing(self) -> Generator[OngoingIterData, None, None]:
        return super().walk_ongoing()

    def _search_parse(self, markup: str) -> List["SearchResult"]:
        soup = self._soup(markup)
        lst = []
        for article in soup.find("div", class_="floats clearfix").find_all(
            "article", attrs={"class": "short clearfix", "id": "short"}
        ):
            for tc_item, short_poster in zip(
                article.find_all("a", class_="tc-item"),
                article.find_all("a", attrs={"class": "short-poster img-box"}),
            ):
                data = {
                    "url": tc_item["href"],
                    "title": tc_item.find("div", class_="tc-title").get_text(strip=True),
                    "poster": "https://animania.online" + short_poster.find("img")["src"],
                }
                lst.append(SearchResult(**data))
        return lst

    def search(self, query: str) -> List["SearchResult"]:
        response = (
            self.HTTP()
            .get(
                f"{self.BASE_URL}/index.php",
                params={"do": "search", "subaction": "search", "story": query},
            )
            .text
        )
        return self._search_parse(response)

    def _ongoing_parse(self, response: str):
        divs_ksupdate = self._soup(response).find_all(
            "div", class_="ksupdate_block_list_item_inner"
        )
        ongs = []
        for div in divs_ksupdate:
            ksupdate_block = div.find("a", class_="ksupdate_block_list_link")
            data = {
                "url": "https://animania.online" + ksupdate_block["href"],
                "name": ksupdate_block.get_text(strip=True),
                "info": div.find("span").get_text(strip=True),
            }
            ongs.append(Ongoing(**data))
        return ongs

    def ongoing(self) -> List["Ongoing"]:
        response = self.HTTP().get(f"{self.BASE_URL}/index.php")
        return self._ongoing_parse(response.text)

    async def async_search(self, query: str) -> List["SearchResult"]:
        async with self.HTTP_ASYNC() as session:
            response = (
                await session.get(
                    f"{self.BASE_URL}/index.php",
                    params={"do": "search", "subaction": "search", "story": query},
                )
            ).text
            return self._search_parse(response)

    async def async_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as session:
            response = await session.get(f"{self.BASE_URL}/index.php")
            return self._ongoing_parse(response.text)


class AnimeInfoParser(BaseModel):
    url: str

    def _parse_meta(self, response: str) -> "AnimeInfo":
        soup = self._soup(response)
        info = soup.find("div", class_="fmright")
        meta_data = {
            "poster": "https://animania.online"
            + soup.find("div", class_="fmid")
            .find("div", attrs={"class": "fposterik-l"})
            .find("img")["data-src"],
            "title": info.find("div", attrs={"class": "fdesc-title"}).get_text(),
            "description": info.find(
                "div", attrs={"class": "fdesc slice-this ficon clearfix"}
            ).get_text(strip=True),
            "meta": [
                li.get_text(strip=True)
                for li in info.find("div", class_="flist clearfix").find_all("li")
            ],
        }
        # dubs_meta
        dubs_id_table = {
            int(
                span["onclick"].replace("kodikSlider.season('", "").replace("', this)", "")
            ): span.get_text()
            for span in soup.find("div", id="ks-translations").find_all("span")
        }

        # video
        # episodes = {name: [{id: 0, video, dub}, ...], ...}
        episodes: dict[str, list[dict]] = {}
        for ul in soup.find("ul", id="ks-episodes"):
            for span in ul.find_all("span"):
                data = {
                    "id": int(ul["id"].replace("season", "")),
                    "name": span.get_text(strip=True),
                    "url": "https:"
                    + span["onclick"].replace("kodikSlider.player('", "").replace("', this);", ""),
                }
                data["dub"] = dubs_id_table.get(data["id"])
                if episodes.get(data["name"]):
                    episodes[data["name"]].append(data)
                else:
                    episodes[data["name"]] = [data]
        return AnimeInfo(**meta_data, _episodes=episodes)

    def get_anime(self) -> "AnimeInfo":
        response = self._HTTP().get(self.url).text
        return self._parse_meta(response)

    async def a_get_anime(self) -> "AnimeInfo":
        async with self._HTTP_ASYNC() as session:
            response = (await session.get(self.url)).text
            return self._parse_meta(response)


class SearchResult(AnimeInfoParser, BaseSearchResult):
    title: str
    poster: str

    def __iter__(self) -> Generator[SearchIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[SearchIterData, None]:
        return super().__aiter__()

    def __str__(self):
        return f"{self.title}"


class Ongoing(AnimeInfoParser, BaseOngoing):
    name: str
    info: str

    def __iter__(self) -> Generator[OngoingIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().__aiter__()

    def __str__(self):
        return f"{self.name}"


class AnimeInfo(BaseAnimeInfo):
    title: str
    description: str
    meta: str
    _episodes: Dict[str, List[Dict]]

    async def a_get_episodes(self) -> List["Episode"]:
        return [Episode(name=name, _video_meta=meta) for name, meta in self._episodes.items()]

    def get_episodes(self) -> List["Episode"]:
        return [Episode(name=name, _video_meta=meta) for name, meta in self._episodes.items()]

    def __str__(self):
        return f"{self.title}\n{self.description}"


class Episode(BaseEpisode):
    name: str
    _video_meta: List[Dict]

    async def a_get_videos(self) -> List["Video"]:
        return [Video(**meta) for meta in self._video_meta]

    def get_videos(self) -> List["Video"]:
        return [Video(**meta) for meta in self._video_meta]

    def __str__(self):
        return self.name


class Video(BaseVideo):
    id: int
    name: str
    dub: str
    __CMP_KEYS__ = ("dub",)


class TestCollections(BaseTestCollections):
    def test_search(self):
        result = Extractor().search("serial experiments lain")
        res = result[0].get_anime().dict()
        assert res.get("poster")
        assert "Эксперименты Лэйн" in res.get("title")

    def test_ongoing(self):
        assert len(Extractor().ongoing()) > 1

    def test_extract_metadata(self):
        for meta in Extractor().search("serial experiments lain")[0]:
            assert (
                meta.search.url
                == "https://animania.online/9403-jeksperimenty-ljejn-serial-experiments-lain-1998-smotret-onlajn.html"
            )
            assert meta.anime.title == 'Сюжет аниме "Эксперименты Лэйн":'
            assert meta.episode.name == "1 серия"
            break

    def test_extract_video(self):
        for meta in Extractor().search("serial experiments lain")[0]:
            assert "kodik" in meta.video.url
            assert meta.video.get_source()[0].url.endswith(".m3u8")
