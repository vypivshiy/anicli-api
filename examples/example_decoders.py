"""at the moment, this module support kodik and aniboom decoders"""
from anicli_api.decoders import Aniboom, Kodik
if __name__ == "__main__":
    print("get videos from kodik")
    kodik_links = Kodik.parse(
        "https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p"
    )
    print(kodik_links)
    for video in kodik_links:
        print(video.quality, video.url)
    print("get videos from aniboom")

    aniboom_links = Aniboom.parse("https://aniboom.one/embed/N9QdKm4Mwz1?episode=1&translation=2")
    for video in aniboom_links:
        # required headers contains in extra_headers attribute:
        # example commands for play video or download:
        # ffmpeg -user_agent 'Mozilla 5.0' -referer 'https://aniboom.one/' -headers 'accept-language: ru-RU' -i 'URL' out.mp4
        # mpv 'URL' -http-header-fields "Referer: https://aniboom.one,Accept-Language: ru-RU, User-Agent:Mozilla 5.0"
        print(video.quality, video.url, video.extra_headers)
