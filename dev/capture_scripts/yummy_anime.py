"""Минимальный скрипт для записи запросов через mitmproxy для yummy_anime

Реализован, чтобы перехватить запросы для дальнейшей конвертации в swagger конфигурацию

API base: https://api.yani.tv
Swagger: https://yummy-anime.ru/api/swagger
"""

from httpx import Client

# mitmproxy for capture traffic (default 8080 port)
PROXY = "https://127.0.0.1:8080"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

# обязательно выключить verify, у нас самоподписанный сертификат!
CLIENT = Client(verify=False, proxy=PROXY, headers=HEADERS)

BASE_URL = "https://api.yani.tv"


def main():
    # 1. FILTER ANIME (search)
    CLIENT.get(f"{BASE_URL}/anime", params={"q": "man", "offset": 0, "limit": 20})
    CLIENT.get(f"{BASE_URL}/anime", params={"q": "lai", "offset": 0, "limit": 20})
    CLIENT.get(f"{BASE_URL}/anime", params={"q": "isekai", "offset": 0, "limit": 20})

    # empty search result
    CLIENT.get(f"{BASE_URL}/anime", params={"q": "doesnotexiststitlename", "offset": 0, "limit": 20})

    # 2. DEDICATED SEARCH (min 3 chars)
    CLIENT.get(f"{BASE_URL}/search", params={"q": "man"})
    CLIENT.get(f"{BASE_URL}/search", params={"q": "isekai"})

    # 3. SCHEDULE (ongoings)
    CLIENT.get(f"{BASE_URL}/anime/schedule")

    # 4. FILTER BY IDS (ongoing -> anime)
    CLIENT.get(f"{BASE_URL}/anime", params={"ids": [1, 2, 3]})

    # 5. ANIME VIDEOS (episodes)
    # not valid id
    CLIENT.get(f"{BASE_URL}/anime/100000000/videos")
    # valid ids
    CLIENT.get(f"{BASE_URL}/anime/1/videos")
    CLIENT.get(f"{BASE_URL}/anime/3/videos")

    # 6. CATALOG (genres, types, default items)
    CLIENT.get(f"{BASE_URL}/anime/catalog")

    # 7. GENRES
    CLIENT.get(f"{BASE_URL}/anime/genres")
    CLIENT.get(f"{BASE_URL}/anime/genres/senen")

    # 8. COUNTS BY TYPES
    CLIENT.get(f"{BASE_URL}/anime/counts/types")


if __name__ == "__main__":
    main()
