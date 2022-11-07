"""at the moment, this module support kodik and aniboom decoders"""
from anicli_api.decoders import Aniboom, Kodik


if __name__ == '__main__':
    kodik_links = Kodik.parse("https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p")
    aniboom_links = Aniboom.parse('https://aniboom.one/embed/N9QdKm4Mwz1?episode=1&translation=2')
    print(kodik_links)
    print(aniboom_links)
