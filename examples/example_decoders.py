"""at the moment, this module support kodik and aniboom decoders"""
from anicli_api.decoders import Aniboom, Kodik
if __name__ == "__main__":
    print("get videos from kodik")
    kodik_links = Kodik.parse(
        "https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p"
    )
    print(kodik_links)
    print("get videos from aniboom")
    # for playing video from aniboom required extra headers:
    # user-agent: any desktop or mobile
    # referer: https://aniboom.one/
    # accept-language: ru-RU  # increase download speed
    # example commands:
    # ffmpeg -user_agent 'Mozilla 5.0' -referer 'https://aniboom.one/' -headers 'accept-language: ru-RU' -i 'URL' out.mp4
    # mpv 'URL' -http-header-fields "Referer: https://aniboom.one,Accept-Language: ru-RU, User-Agent:Mozilla 5.0"
    aniboom_links = Aniboom.parse("https://aniboom.one/embed/N9QdKm4Mwz1?episode=1&translation=2")
    print(*aniboom_links, sep="\n")
