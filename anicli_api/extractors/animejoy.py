"""Animejoy parser - SUBTITLES ONLY

12.01.2023 works only kodik, sibnet
Todo: add decoders for dzen, mail.ru, etc
TODO reverse ustore (uboost.one), alloha players
TODO add mailru
TODO add yt-dlp proxy
TODO reverse ebd.cda.pl (not work in RU region)
"""
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
    # IDE typing help: SearchResult.__iter__, SearchResult.__aiter__, walk_search, async_walk_search
    search: SearchResult
    anime: AnimeInfo
    episode: Episode
    video: Video


class OngoingIterData(Protocol):
    # IDE typing help: typing help: Ongoing.__iter__, Ongoing.__aiter__, walk_ongoing, async_walk_ongoing
    search: Ongoing
    anime: AnimeInfo
    episode: Episode
    video: Video


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here
    BASE_URL = "https://animejoy.ru"

    def async_walk_search(self, query: str) -> AsyncGenerator[SearchIterData, None]:
        return super().async_walk_search(query)

    def walk_search(self, query: str) -> Generator[SearchIterData, None, None]:
        return super().walk_search(query)

    def async_walk_ongoing(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().async_walk_ongoing()

    def walk_ongoing(self) -> Generator[OngoingIterData, None, None]:
        return super().walk_ongoing()

    def search(self, query: str) -> List["SearchResult"]:
        response = (
            self.HTTP()
            .post(self.BASE_URL, data={"story": query, "do": "search", "subaction": "search"})
            .text
        )
        soup = self._soup(response)
        titles = soup.find_all("h2", class_="ntitle")
        return [
            SearchResult(name=title.get_text(strip=True), url=title.find("a")["href"])
            for title in titles
        ]

    def ongoing(self) -> List["Ongoing"]:
        response = self.HTTP().get(f"{self.BASE_URL}/ongoing/").text
        soup = self._soup(response)
        titles = soup.find_all("h2", class_="ntitle")
        return [
            Ongoing(name=title.get_text(strip=True), url=title.find("a")["href"])
            for title in titles
        ]

    async def async_search(self, query: str) -> List["SearchResult"]:
        async with self.HTTP_ASYNC() as session:
            response = (
                await session.post(
                    self.BASE_URL, data={"story": query, "do": "search", "subaction": "search"}
                )
            ).text
            soup = self._soup(response)
            titles = soup.find_all("h2", class_="ntitle")
            return [
                SearchResult(name=title.get_text(strip=True), url=title.find("a")["href"])
                for title in titles
            ]

    async def async_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as session:
            response = (await session.get(f"{self.BASE_URL}/ongoing")).text
            soup = self._soup(response)
            titles = soup.find_all("h2", class_="ntitle")
            return [
                Ongoing(name=title.get_text(strip=True), url=title.find("a")["href"])
                for title in titles
            ]


class AnimeInfoParser(BaseModel):
    name: str
    url: str

    def _parse_metadata(self, response: str):
        soup = self._soup(response)
        name = soup.find("h1", class_="h2 ntitle").get_text(strip=True)
        roman_name = soup.find("h2", class_="romanji").get_text(strip=True)
        description = soup.find("div", class_="pcdescrf").get_text(strip=True)
        anime_id = self.url.split("/")[-1].split("-")[0]
        # todo decode metadata
        metadata_lst = [
            p_zerop.get_text(strip=True) for p_zerop in soup.find_all("p", class_="zerop")
        ]
        metadata = {}
        for p_zerop in metadata_lst:
            try:
                key, value = p_zerop.split(":")
                metadata[key] = value
            except ValueError:
                continue
        return AnimeInfo(
            name=name,
            roman_name=roman_name,
            description=description,
            anime_id=anime_id,
            metadata=metadata,
        )

    async def a_get_anime(self) -> "AnimeInfo":
        async with self._HTTP_ASYNC() as session:
            response = await session.get(self.url)
            return self._parse_metadata(response.text)

    def get_anime(self) -> "AnimeInfo":
        response = self._HTTP().get(self.url)
        return self._parse_metadata(response.text)


class SearchResult(AnimeInfoParser, BaseSearchResult):
    def __iter__(self) -> Generator[SearchIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[SearchIterData, None]:
        return super().__aiter__()


class Ongoing(AnimeInfoParser, BaseOngoing):
    def __iter__(self) -> Generator[OngoingIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().__aiter__()


class AnimeInfo(BaseAnimeInfo):
    name: str
    roman_name: str
    description: str
    anime_id: str
    metadata: dict[str, str]

    @staticmethod
    def _parse_playlist_list(soup) -> Dict[str, str]:
        playlist_list = soup.find("div", class_="playlists-lists").find_all(
            "div", class_="playlists-items"
        )
        # create dict form {data-id: hosting-name}
        playlist_names: dict[str, str] = {}
        for playlist_item in playlist_list:
            for li_file in playlist_item.find_all("li"):
                playlist_names[li_file["data-id"]] = li_file.get_text(strip=True)
        return playlist_names

    @staticmethod
    def _parse_playlist_videos(soup, playlist_names: Dict[str, str]) -> Dict[str, List[str]]:
        playlist_videos = soup.find("div", class_="playlists-videos").find(
            "div", class_="playlists-items"
        )
        playlist: dict[str, list[str]] = {}
        # create dict {hosting-name: [video_1, video_2, ...], ...}
        for li_file in playlist_videos.find_all("li"):
            data_id = li_file["data-id"]
            url: str = li_file["data-file"]
            if not url.startswith("https:") and url.startswith("//"):
                url = f"https:{url}"
            if not playlist.get(playlist_names.get(data_id)):  # type: ignore
                playlist[playlist_names.get(data_id)] = []  # type: ignore
            playlist[playlist_names.get(data_id)].append(url)  # type: ignore
        return playlist

    def _parse_response(self, response: str) -> List["Episode"]:
        soup = self._soup(response)
        playlist_names = self._parse_playlist_list(soup)
        playlist = self._parse_playlist_videos(soup, playlist_names)
        # {1: [{url: ..., hosting: ...}, 2:{...}, ...]
        episodes: dict[int, list[dict[str, str]]] = {}
        for hosting, videos in playlist.items():
            for i, video in enumerate(videos):
                if not episodes.get(i):
                    episodes[i] = []
                episodes[i].append({"url": video, "hosting": hosting})
        return [Episode(num=num, videos=videos) for num, videos in episodes.items()]

    async def a_get_episodes(self) -> List["Episode"]:
        async with self._HTTP_ASYNC() as session:
            response = (
                await session.get(
                    "https://animejoy.ru/engine/ajax/playlists.php",
                    params={"news_id": self.anime_id, "xfield": "playlist"},
                )
            ).json()["response"]
            return self._parse_response(response)

    def get_episodes(self) -> List["Episode"]:
        response = (
            self._HTTP()
            .get(
                "https://animejoy.ru/engine/ajax/playlists.php",
                params={"news_id": self.anime_id, "xfield": "playlist"},
            )
            .json()["response"]
        )
        return self._parse_response(response)


class Episode(BaseEpisode):
    num: int
    videos: list[dict[str, str]]

    async def a_get_videos(self) -> List["Video"]:
        return [Video(url=video["url"], hosting=video["hosting"]) for video in self.videos]

    def get_videos(self) -> List["Video"]:
        return [Video(url=video["url"], hosting=video["hosting"]) for video in self.videos]

    def __str__(self):
        return f"Subtitles [{', '.join([v['hosting'] for v in self.videos])}]"


class Video(BaseVideo):
    hosting: str

    __CMP_KEYS__ = ("hosting",)

    def __hash__(self):
        return hash(self.hosting)


class TestCollections(BaseTestCollections):
    def test_search(self):
        result = Extractor().search("serial experiments lain")
        assert result[0].get_anime().anime_id == "2789"

    def test_ongoing(self):
        # test get ongoing
        assert len(Extractor().ongoing()) > 1

    def test_extract_metadata(self):
        # rewrite testcase get metadata here
        for meta in Extractor().search("serial experiments lain")[0]:
            # past metadata dict here
            assert meta.search.url == "https://animejoy.ru/tv-serialy/2789-eksperimenty-leyn.html"
            assert meta.anime.anime_id == "2789"
            assert meta.episode.num == 0
            break

    def test_extract_video(self):
        # rewrite testcase extract video here
        result = Extractor().search("serial experiments lain")[0]
        episodes = result.get_anime().get_episodes()
        videos = episodes[0].get_videos()
        for video in videos:
            assert video.hosting in ("Sibnet", "OK", "Mail")
