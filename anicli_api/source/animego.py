from typing import Dict, List

from parsel import Selector
from scrape_schema import ScField
from scrape_schema.callbacks.parsel import crop_by_xpath_all as cbxa
from scrape_schema.callbacks.parsel import get_attr, get_text, replace_text
from scrape_schema.fields.parsel import ParselXPath, ParselXPathList

from anicli_api.base import (
    BaseAnime,
    BaseEpisode,
    BaseExtractor,
    BaseOngoing,
    BaseSearch,
    BaseSource,
)


class Extractor(BaseExtractor):
    BASE_URL = "https://animego.org/"

    def search(self, query: str) -> List["Search"]:
        response = self.HTTP().get(f"{self.BASE_URL}search/anime", params={"q": query})
        return Search.from_crop_rule_list(
            response.text,
            crop_rule=cbxa(
                "//div[@class='row']/div[@class='animes-grid-item col-6 col-sm-6 col-md-4 col-lg-3 col-xl-2 col-ul-2']"
            ),
        )

    async def a_search(self, query: str) -> List["Search"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(f"{self.BASE_URL}search/anime", params={"q": query})
            return Search.from_crop_rule_list(
                response.text,
                crop_rule=cbxa(
                    "//div[@class='row']/div[@class='animes-grid-item col-6 col-sm-6 col-md-4 col-lg-3 col-xl-2 col-ul-2']"
                ),
            )

    def ongoing(self) -> List["Ongoing"]:
        response = self.HTTP().get(self.BASE_URL)
        return Ongoing.from_crop_rule_list(
            response.text, crop_rule=cbxa('//*[starts-with(@class, "last-update-item")]')
        )

    async def a_ongoing(self) -> List["Ongoing"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.BASE_URL)
            return Ongoing.from_crop_rule_list(
                response.text, crop_rule=cbxa('//*[starts-with(@class, "last-update-item")]')
            )


class Search(BaseSearch):
    thumbnail: ScField[str, ParselXPath("//a/div", callback=get_attr("data-original"))]
    rating: ScField[
        float,
        ParselXPath(
            "//div[@class='p-rate-flag__text']", default="0", callback=replace_text(",", ".")
        ),
    ]
    name: ScField[
        str, ParselXPath("//div[@class='text-gray-dark-6 small mb-1 d-none d-sm-block']/div")
    ]
    title: ScField[
        str,
        ParselXPath(
            "//div[@class='h5 font-weight-normal mb-2 card-title text-truncate']/a",
            callback=get_attr("title"),
        ),
    ]
    url: ScField[
        str,
        ParselXPath(
            "//div[@class='h5 font-weight-normal mb-2 card-title text-truncate']/a",
            callback=get_attr("href"),
        ),
    ]

    def get_anime(self) -> "Anime":
        response = self.HTTP().get(self.url)
        return Anime(response.text)

    async def a_get_anime(self) -> "Anime":
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            return Anime(response.text)


class Ongoing(BaseOngoing):
    _thumb_style: ScField[
        str, ParselXPath("//div[@class='img-square lazy br-50']", callback=get_attr("style"))
    ]
    title: ScField[str, ParselXPath("//span[@class='last-update-title font-weight-600']")]
    episode: ScField[str, ParselXPath("//div[@class='font-weight-600 text-truncate']")]
    dub: ScField[
        str, ParselXPath("//div[@class='ml-3 text-right']/div[@class='text-gray-dark-6']")
    ]
    _onclick: ScField[str, ParselXPath("//div", callback=get_attr("onclick"))]

    @property
    def thumbnail(self):
        return self._thumb_style.replace("background-image: url(", "").replace(");", "")

    @property
    def url(self):
        path = self._onclick.replace("location.href='", "").replace("'", "")
        return f"https://animego.org{path}"

    @property
    def num(self):
        return int(self.episode.replace(" серия", "").replace(" Серия", ""))

    def get_anime(self) -> "Anime":
        response = self.HTTP().get(self.url)
        return Anime(response.text)

    async def a_get_anime(self) -> "Anime":
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            return Anime(response.text)


class Anime(BaseAnime):
    rating: ScField[
        float,
        ParselXPath(
            '//*[@id="itemRatingBlock"]/div[1]/div[2]/div[1]/span[1]',
            default="0",
            callback=replace_text(",", "."),
        ),
    ]
    title: ScField[str, ParselXPath("//div[@class='anime-title']/div/h1")]
    alt_titles: ScField[List[str], ParselXPathList('//ul[@class="list-unstyled small mb-0"]/li')]
    # todo create normal structure
    _raw_metadata: ScField[
        str,
        ParselXPath(
            '//div[@class="anime-info"]/dl[@class="row"]',
            callback=get_text(strip=True, deep=True, sep=" "),
        ),
    ]
    url: ScField[str, ParselXPath("//html/head/link[@rel='canonical']", callback=get_attr("href"))]
    description: ScField[
        str,
        ParselXPath(
            "//div[@class='description pb-3']", callback=get_text(strip=True, sep=" ")
        ),  # mobile agent
        ParselXPath("//div[@data-readmore='content']", callback=get_text(strip=True, sep=" ")),
    ]  # desktop agent

    @property
    def anime_id(self) -> str:
        return self.url.split("-")[-1]

    @staticmethod
    def _get_dubbers(response: str) -> Dict[str, str]:
        sel = Selector(response)
        dubbers_id: List[str] = ParselXPathList(
            '//*[@id="video-dubbing"]/span', callback=get_attr("data-dubbing")
        ).extract(sel, type_=List[str])
        dubbers_name: List[str] = ParselXPathList(
            '//*[@id="video-dubbing"]/span', callback=get_text(deep=True, strip=True)
        ).extract(sel)
        return dict(zip(dubbers_id, dubbers_name))

    def get_episodes(self) -> List["Episode"]:
        response = (
            self.HTTP()
            .get(f"https://animego.org/anime/{self.anime_id}/player?_allow=true")
            .json()["content"]
        )

        _dubbers_table = self._get_dubbers(response)
        return Episode.from_crop_rule_list(
            response,
            crop_rule=cbxa('//*[@id="video-carousel"]/div/div'),
            _dubbers_table=_dubbers_table,
        )

    async def a_get_episodes(self) -> List["Episode"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(self.url)
            _dubbers_table = self._get_dubbers(response)
            return Episode.from_crop_rule_list(
                response,
                crop_rule=cbxa('//*[@id="video-carousel"]/div/div'),
                _dubbers_table=_dubbers_table,
            )


class Episode(BaseEpisode):
    num: ScField[int, ParselXPath("//div", callback=get_attr("data-episode"))]
    _episode_type: ScField[int, ParselXPath("//div", callback=get_attr("data-episode-type"))]
    data_id: ScField[int, ParselXPath("//div", callback=get_attr("data-id"))]
    title: ScField[str, ParselXPath("//div", callback=get_attr("data-episode-title"))]
    released: ScField[str, ParselXPath("//div", callback=get_attr("data-episode-released"))]
    _dubbers_table: Dict[str, str]

    def get_sources(self) -> List["Source"]:
        response = (
            self.HTTP()
            .get(
                "https://animego.org/anime/series",
                params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.data_id},
            )
            .json()["content"]
        )
        return Source.from_crop_rule_list(
            response,
            crop_rule=cbxa(
                '//*[@id="video-players"]/span',
            ),
            _dubbers_table=self._dubbers_table,
        )

    async def a_get_sources(self) -> List["Source"]:
        async with self.HTTP_ASYNC() as client:
            response = await client.get(
                "https://animego.org/anime/series",
                params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.data_id},
            ).json()["content"]
            return Source.from_crop_rule_list(
                response,
                crop_rule=cbxa(
                    '//*[@id="video-players"]/span',
                ),
                _dubbers_table=self._dubbers_table,
            )


class Source(BaseSource):
    _dubbers_table: Dict[str, str]
    _url: ScField[str, ParselXPath("//span", callback=get_attr("data-player"))]
    _data_provider: ScField[str, ParselXPath("//span", callback=get_attr("data-provider"))]
    _data_provide_dubbing: ScField[
        str, ParselXPath("//span", callback=get_attr("data-provide-dubbing"))
    ]
    name: ScField[str, ParselXPath("//span/span")]

    @property
    def url(self):
        return f"https:{self._url}"

    @property
    def dub(self):
        return self._dubbers_table.get(self._data_provide_dubbing)

    def get_videos(self):
        pass

    async def a_get_videos(self):
        pass
