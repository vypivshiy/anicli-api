"""player hosts video in mailru cdn servers"""

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
    # 1. first request SSR:
    # client.get('https://animego.me/cdn-iframe/60254/Dream%20Cast/1/1', headers={'referer': 'https://animego.me'})
    # and extract:
    # <div class="player-cvh">
    # <video-player
    #             id="pcvh"
    #             data-title-id="60254"  // id=
    #             data-publisher-id="746"  // pub=746
    #             ident="cvh"
    #             data-aggregator="mali"  // aggr=
    #             is-show-voice-only="true"
    #             is-show-banner="true"
    #                                     episode="1"
    #                         priority-voice="Dream Cast"
    #     ></video-player>

    # Обычные дни Яно
    # full playlist
    CLIENT.get("https://plapi.cdnvideohub.com/api/v1/player/sv/playlist?pub=746&aggr=mali&id=60254")

    # videos
    CLIENT.get("https://plapi.cdnvideohub.com/api/v1/player/sv/video/10179336100592")


if __name__ == "__main__":
    main()
