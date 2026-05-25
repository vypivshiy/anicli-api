"""Минимальный скрипт для записи запросов через mitmproxy для aniliberty

Реализован, чтобы перехватить запросы для дальнейшей конвертации в swagger конфигурацию

API docs: https://aniliberty.top/api/docs/v1
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

BASE_URL = "https://aniliberty.top/api/v1"


def main():
    # 1. SEARCH API (catalog releases with search filter)
    CLIENT.get(f"{BASE_URL}/anime/catalog/releases", params={"f[search]": "man"})
    CLIENT.get(f"{BASE_URL}/anime/catalog/releases", params={"f[search]": "lai"})
    CLIENT.get(f"{BASE_URL}/anime/catalog/releases", params={"f[search]": "isekai"})

    # empty search result
    CLIENT.get(f"{BASE_URL}/anime/catalog/releases", params={"f[search]": "doesnotexiststitlename"})

    # 2. ONGOINGS (catalog releases without filters)
    CLIENT.get(f"{BASE_URL}/anime/catalog/releases")

    # 3. SEARCH via dedicated search endpoint
    CLIENT.get(f"{BASE_URL}/app/search/releases", params={"query": "man"})
    CLIENT.get(f"{BASE_URL}/app/search/releases", params={"query": "isekai"})

    # 4. GET release by id (with episodes)
    # any valid release id from search results
    CLIENT.get(f"{BASE_URL}/anime/releases/1", params={"include": "id,episodes"})

    # 5. GET single episode by id
    CLIENT.get(f"{BASE_URL}/anime/releases/episodes/1")

    # 6. APP STATUS
    CLIENT.get(f"{BASE_URL}/app/status")


if __name__ == "__main__":
    main()
