"""Минимальный скрипт для записи запросов через mitmproxy для animevost

Реализован, чтобы перехватить запросы для дальнейшей конвертации в swagger конфигурацию
"""

from httpx import Client

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

# обязательно выключить verify, у нас самоподписанный сертификат!
CLIENT = Client(verify=False, proxy=PROXY, headers=HEADERS)


def main():
    # 1. SEARCH API
    # any search result
    CLIENT.post("https://api.animevost.org/v1/search", data={"name": "man"})
    CLIENT.post("https://api.animevost.org/v1/search", data={"name": "lai"})
    CLIENT.post("https://api.animevost.org/v1/search", data={"name": "isekai"})

    # empty result search
    CLIENT.post("https://api.animevost.org/v1/search", data={"name": "doesnotexiststitlename"})
    # 2. ONGOINGS list
    CLIENT.get("https://api.animevost.org/v1/last", params={"page": 1, "quantity": 20})

    # 3. get episodes (1 not valid, 3 valid ids)

    # not valid playlist
    CLIENT.post("https://api.animevost.org/v1/playlist", data={"id": 100_000_000})

    # Хиромен / Heroman [1-26 из 26]
    CLIENT.post("https://api.animevost.org/v1/playlist", data={"id": 1568})

    # Сэкэй, который рисует демонов / Sekiei Ayakashi Mangatan [1-3 из 3]
    CLIENT.post("https://api.animevost.org/v1/playlist", data={"id": 393})

    # Вампир не умеет правильно сосать кровь / Chanto Suenai Kyuuketsuki-chan [1-4 из 12+]
    CLIENT.post("https://api.animevost.org/v1/playlist", data={"id": 3668})


if __name__ == "__main__":
    main()
