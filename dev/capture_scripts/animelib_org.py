"""NOTE:

- На момент исследований, авторизация через вк не работала в https://animelib.org
    - но работает на старом домене https://anilib.me и он совместим с API
- Требуется авторизация для получения bearer токена для извлечения видео с их оригинального плеера, иначе доступен только kodik
https://github.com/vypivshiy/anicli-api/issues/42
"""

from httpx import Client, BaseTransport, HTTPTransport, Request, Response, Timeout
import os
from time import sleep

BEARER_TOKEN = os.environ.get("ANILIB_TOKEN", None)

# mitmproxy for capture traffic (default 8080 port)
PROXY = "https://127.0.0.1:8080"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    # Often, XMLHttpRequest header required
    "x-requested-with": "XMLHttpRequest",
    "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}
if BEARER_TOKEN:
    HEADERS["Authorization"] = f"Bearer {BEARER_TOKEN}"


# слишком много запросов в наборе, надо принудительно замедлить
class DelayedTransport(BaseTransport):
    def __init__(self, delay: float = 1, **transport_options):
        self._delay = delay
        self._inner = HTTPTransport(**transport_options)

    def handle_request(self, request: Request) -> Response:
        sleep(self._delay)
        response = self._inner.handle_request(request)
        return response


# обязательно выключить verify, у нас самоподписанный сертификат!
CLIENT = Client(
    headers=HEADERS,
    follow_redirects=True,
    timeout=Timeout(60.0),
    transport=DelayedTransport(delay=2.5, verify=False, proxy=PROXY, http2=True),
)


# params constants
_SEARCH_ANIME_FIELD_PARAMS = ["rate", "rate_avg", "releaseDate"]
_GET_ANIME_FIELD_PARAMS = [
    "background",
    "eng_name",
    "otherNames",
    "summary",
    "releaseDate",
    "type_id",
    "caution",
    "views",
    "close_view",
    "rate_avg",
    "rate",
    "genres",
    "tags",
    "teams",
    "user",
    "franchise",
    "authors",
    "publisher",
    "userRating",
    "moderated",
    "metadata",
    "metadata.count",
    "metadata.close_comments",
    "anime_status_id",
    "time",
    "episodes",
    "episodes_count",
    "episodesSchedule",
    "shiki_rate",
]
_SITE_ID = [1, 3]


def main():
    # 1. SEARCH API
    # any search result

    CLIENT.get(
        "https://api.cdnlibs.org/api/anime",
        params={"fields[]": _SEARCH_ANIME_FIELD_PARAMS, "site_id[]": _SITE_ID, "q": "man"},
    )
    CLIENT.get(
        "https://api.cdnlibs.org/api/anime",
        params={"fields[]": _SEARCH_ANIME_FIELD_PARAMS, "site_id[]": _SITE_ID, "q": "lai"},
    )
    CLIENT.get(
        "https://api.cdnlibs.org/api/anime",
        params={"fields[]": _SEARCH_ANIME_FIELD_PARAMS, "site_id[]": _SITE_ID, "q": "isekai"},
    )

    # empty result search
    CLIENT.get(
        "https://api.cdnlibs.org/api/anime",
        params={"fields[]": _SEARCH_ANIME_FIELD_PARAMS, "site_id[]": _SITE_ID, "q": "doesnotexiststitlename"},
    )
    CLIENT.get(
        "https://api.cdnlibs.org/api/anime",
        params={
            "page": 1,
            "status[]": [1],  # magic enum - get ongoings
            "fields[]": ["rate", "rate_avg", "userBookmark"],
            "site_id[]": _SITE_ID,
            "sort_by": "last_episode_at",
        },
    )

    # get anime  (by slug)
    # 1. Эксперименты Лэйн Serial Experiments Lain
    CLIENT.get(
        "https://api.cdnlibs.org/api/anime/316--serial-experiments-lain-anime",
        params={"fields[]": _GET_ANIME_FIELD_PARAMS},
    )

    # 2. семья шпиона 1
    CLIENT.get(
        "https://api.cdnlibs.org/api/anime/19521--spy-x-family-anime", params={"fields[]": _GET_ANIME_FIELD_PARAMS}
    )

    # 3. Неумелый сэмпай Bukiyou na Senpai.
    CLIENT.get(
        "https://api.cdnlibs.org/api/anime/24836--bukiyou-na-senpai-anime", params={"fields[]": _GET_ANIME_FIELD_PARAMS}
    )

    # 4. not exists
    CLIENT.get("https://api.cdnlibs.org/api/anime/0--does-not-exists", params={"fields[]": _GET_ANIME_FIELD_PARAMS})

    # EPISODES
    # "data": [{ "id": 21286, ...}, ... ]
    CLIENT.get("https://api.cdnlibs.org/api/episodes", params={"anime_id": "19521--spy-x-family-anime"})
    CLIENT.get("https://api.cdnlibs.org/api/episodes", params={"anime_id": "316--serial-experiments-lain-anime"})

    # not exists
    CLIENT.get("https://api.cdnlibs.org/api/episodes", params={"anime_id": "0--does-not-exists"})

    # get player and dubbers by prev episode_id

    # Эксперименты Лэйн Serial Experiments Lain
    CLIENT.get("https://api.cdnlibs.org/api/episodes/9921")
    CLIENT.get("https://api.cdnlibs.org/api/episodes/9922")
    CLIENT.get("https://api.cdnlibs.org/api/episodes/9923")

    # spy family 1
    CLIENT.get("https://api.cdnlibs.org/api/episodes/71144")
    CLIENT.get("https://api.cdnlibs.org/api/episodes/71145")
    CLIENT.get("https://api.cdnlibs.org/api/episodes/71146")

    # NOT valid
    CLIENT.get("https://api.cdnlibs.org/api/episodes/1000009920")


if __name__ == "__main__":
    main()
