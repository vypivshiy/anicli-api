from __future__ import annotations
from typing import List, cast


from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.source.parsers.animelib_org_parser import AnimelibOrgApi

# types
from anicli_api.source.parsers.animelib_org_parser import (
    AnimeListResponseJson,
    AnimeDetailResponseJson,
    EpisodeListItemJson,
    PlayerJson,
    AnimeListItemJson,
    AnimeDetailJson,
    EpisodeListResponseJson,
    EpisodeDetailResponseJson,
)


# consts for API requests
# params constants
_SEARCH_ANIME_FIELD_PARAMS = ["rate", "rate_avg", "releaseDate"]
_SITE_ID = [1, 3]


class Extractor(BaseExtractor):
    BASE_URL = "https://api.cdnlibs.org/api/"

    def search(self, query: str) -> list["Search"]:
        result = AnimelibOrgApi.list_anime(
            self.http, fields=["rate", "rate_avg", "releaseDate"], site_id=[1, 3], q=query
        )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(AnimeListResponseJson, value)
        results = [
            Search(
                title=data.get("rus_name", "") or data.get("name", "") or data.get("eng_name", ""),
                thumbnail=data["cover"]["default"],
                url=data["slug_url"],  # stub
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    async def a_search(self, query: str) -> list["Search"]:
        result = await AnimelibOrgApi.async_list_anime(
            self.http_async, fields=["rate", "rate_avg", "releaseDate"], site_id=[1, 3], q=query
        )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(AnimeListResponseJson, value)
        results = [
            Search(
                title=data.get("rus_name", "") or data.get("name", "") or data.get("eng_name", ""),
                thumbnail=data["cover"]["default"],
                url=data["slug_url"],  # stub
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    def ongoing(self) -> list["Ongoing"]:
        # status - magic enum. sorts by ongoings
        result = AnimelibOrgApi.list_anime(
            self.http,
            fields=["rate", "rate_avg", "userBookmark"],
            site_id=[1, 3],
            status=[1],
            sort_by="last_episode_at",
        )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(AnimeListResponseJson, value)
        results = [
            Ongoing(
                title=data.get("rus_name", "") or data.get("name", "") or data.get("eng_name", ""),
                thumbnail=data["cover"]["default"],
                url=data["slug_url"],  # stub
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    async def a_ongoing(self) -> list["Ongoing"]:
        # status - magic enum. sorts by ongoings
        result = await AnimelibOrgApi.async_list_anime(
            self.http_async,
            fields=["rate", "rate_avg", "userBookmark"],
            site_id=[1, 3],
            status=[1],
            sort_by="last_episode_at",
        )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(AnimeListResponseJson, value)
        results = [
            Ongoing(
                title=data.get("rus_name", "") or data.get("name", "") or data.get("eng_name", ""),
                thumbnail=data["cover"]["default"],
                url=data["slug_url"],  # stub
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results


@define(kw_only=True)
class Search(BaseSearch):
    data: AnimeListItemJson

    def get_anime(self) -> "Anime":
        result = AnimelibOrgApi.get_anime(self.http, slug_url=self.data["slug_url"])
        if not result.is_ok:
            return
        value = result.value
        value = cast(AnimeDetailResponseJson, value)
        data = value["data"]
        return Anime(
            title=self.title,
            thumbnail=data["cover"]["default"],
            description=data.get("summary", ""),
            data=data,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> BaseAnime:
        result = await AnimelibOrgApi.async_get_anime(self.http_async, slug_url=self.data["slug_url"])
        if not result.is_ok:
            return
        value = result.value
        value = cast(AnimeDetailResponseJson, value)
        data = value["data"]
        return Anime(
            title=self.title,
            thumbnail=data["cover"]["default"],
            description=data.get("summary", ""),
            data=data,
            **self._kwargs_http,
        )


@define(kw_only=True)
class Ongoing(BaseOngoing):
    data: AnimeListItemJson

    def get_anime(self) -> "Anime":
        result = AnimelibOrgApi.get_anime(self.http, slug_url=self.data["slug_url"])
        if not result.is_ok:
            return
        value = result.value
        value = cast(AnimeDetailResponseJson, value)
        data = value["data"]
        return Anime(
            title=self.title,
            thumbnail=data["cover"]["default"],
            description=data.get("summary", ""),
            data=data,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> BaseAnime:
        result = await AnimelibOrgApi.async_get_anime(self.http_async, slug_url=self.data["slug_url"])
        if not result.is_ok:
            return
        value = result.value
        value = cast(AnimeDetailResponseJson, value)
        data = value["data"]
        return Anime(
            title=self.title,
            thumbnail=data["cover"]["default"],
            description=data.get("summary", ""),
            data=data,
            **self._kwargs_http,
        )


@define(kw_only=True)
class Anime(BaseAnime):
    data: AnimeDetailJson

    def get_episodes(self) -> list["Episode"]:
        result = AnimelibOrgApi.list_episodes(self.http, anime_id=self.data["slug_url"])
        if not result.is_ok:
            return []
        value = result.value
        value = cast(EpisodeListResponseJson, value)
        results = [
            Episode(
                title=data.get("name", "") or "Episode",  # maybe empty string
                ordinal=int(data["number"]),
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    async def a_get_episodes(self) -> list["Episode"]:
        result = await AnimelibOrgApi.async_list_episodes(self.http_async, anime_id=self.data["slug_url"])
        if not result.is_ok:
            return []
        value = result.value
        value = cast(EpisodeListResponseJson, value)
        results = [
            Episode(
                title=data.get("name", "") or "Episode",  # maybe empty string
                ordinal=int(data["number"]),
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results


@define(kw_only=True)
class Episode(BaseEpisode):
    data: EpisodeListItemJson

    def get_sources(self) -> list["Source"]:
        result = AnimelibOrgApi.get_episode(self.http, id=self.data["id"])
        if not result.is_ok:
            return []
        value = result.value
        value = cast(EpisodeDetailResponseJson, value)
        results: List[Source] = []
        for data in value["data"]["players"]:
            # //kodik.com/...
            if data["player"].lower() == "kodik":
                results.append(
                    Source(
                        title=data["team"]["name"],
                        url="https:" + data["src"],  # stub
                        data=data,
                        **self._kwargs_http,
                    )
                )
            # spawned if provide auth token
            # NOTE: not implemented change reserve servers
            # https://api.cdnlibs.org/api/constants?
            # fields[]=videoServers&fields[]=animeDistributionId&fields[]=animeDistributionUrl
            elif data["player"].lower() == "animelib":
                results.append(
                    Source(
                        title=data["team"]["name"],
                        url="https://video1.cdnlibs.org/.%D0%B0s/",
                        data=data,
                        **self._kwargs_http,
                    )
                )
        return results

    async def a_get_sources(self) -> list["Source"]:
        result = await AnimelibOrgApi.async_get_episode(self.http_async, id=self.data["id"])
        if not result.is_ok:
            return []
        value = result.value
        value = cast(EpisodeDetailResponseJson, value)
        results: List[Source] = []
        for data in value["data"]["players"]:
            # //kodik.com/...
            if data["player"].lower() == "kodik":
                results.append(
                    Source(
                        title=data["team"]["name"],
                        url="https:" + data["src"],  # stub
                        data=data,
                        **self._kwargs_http,
                    )
                )
            # spawned if provide auth token
            # NOTE: not implemented change reserve servers
            # https://api.cdnlibs.org/api/constants?
            # fields[]=videoServers&fields[]=animeDistributionId&fields[]=animeDistributionUrl
            elif data["player"].lower() == "animelib":
                results.append(
                    Source(
                        title=data["team"]["name"],
                        url="https://video1.cdnlibs.org/.%D0%B0s/",
                        data=data,
                        **self._kwargs_http,
                    )
                )
        return results


@define(kw_only=True)
class Source(BaseSource):
    data: PlayerJson

    def get_videos(self, **httpx_kwargs) -> list[Video]:
        # implemended, run original extractors
        if self.data["player"].lower() == "kodik":
            return super().get_videos(**httpx_kwargs)  # type: ignore

        elif self.data["player"].lower() == "animelib":
            results: List[Video] = []
            # NOTE: 'video' contains only if ['player'] == "animelib"
            for video in self.data["video"]["quality"]:
                results.append(
                    Video(
                        type="mp4",
                        quality=video["quality"],
                        url=self.url + video["href"],
                        headers={"Referrer": "https://v3.animelib.org", "User-Agent": self.http.headers["User-Agent"]},
                    )
                )
            return results
        return []

    async def a_get_videos(self, **httpx_kwargs) -> list[Video]:
        # implemended, run original extractors
        if self.data["player"].lower() == "kodik":
            return super().a_get_videos(**httpx_kwargs)  # type: ignore

        elif self.data["player"].lower() == "animelib":
            results: List[Video] = []
            # NOTE: 'video' contains only if ['player'] == "animelib"
            for video in self.data["video"]["quality"]:
                results.append(
                    Video(
                        type="mp4",
                        quality=video["quality"],
                        url=self.url + video["href"],
                        headers={"Referrer": "https://v3.animelib.org", "User-Agent": self.http.headers["User-Agent"]},
                    )
                )
            return results
        return []


if __name__ == "__main__":
    from anicli_api.tools import cli
    import os

    # allow extract anilib sources if pass auth token
    # you can auth and find token in devtools->XHR->rest-api request
    # headers requests, Authorization key
    # HEADER = {"Authorization": "Bearer ..."}
    # EXTRACTOR = Extractor()
    # EXTRACTOR.http.headers.update(HEADER)
    # cli(EXTRACTOR)
    TOKEN = os.environ.get("ANIMELIB_TOKEN", None)
    ex = Extractor()
    if TOKEN:
        if not TOKEN.startswith("Bearer"):
            TOKEN = f"Bearer {TOKEN}"
        ex.http.headers.update({"Authorization": TOKEN})
    cli(ex)
