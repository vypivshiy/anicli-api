"""Минимальный скрипт для записи запросов через mitmproxy для animevost

Реализован, чтобы перехватить запросы для дальнейшей конвертации в swagger конфигурацию

NOTE:
- для главной страницы (Anime объект) с тайтлом нужно парсить html
- для эпизодов в видео нужно декодировать обфусцированный url плеера
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
    # min search len activate = 4

    # valid search result
    CLIENT.post("https://dreamerscast.com/", data={"search": "gach", "status": "", "pageSize": 16, "pageNumber": 1})
    CLIENT.post("https://dreamerscast.com/", data={"search": "isekai", "status": "", "pageSize": 16, "pageNumber": 1})
    # empty search
    CLIENT.post(
        "https://dreamerscast.com/",
        data={"search": "doesnotexiststitlename", "status": "", "pageSize": 16, "pageNumber": 1},
    )

    # 2. ONGOINGS list (empty search query)
    CLIENT.post("https://dreamerscast.com/", data={"search": "", "status": "", "pageSize": 16, "pageNumber": 1})


if __name__ == "__main__":
    main()
