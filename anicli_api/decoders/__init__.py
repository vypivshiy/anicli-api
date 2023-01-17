from anicli_api.decoders.aniboom import Aniboom
from anicli_api.decoders.animejoy import AnimeJoyDecoder
from anicli_api.decoders.csst import CsstOnline
from anicli_api.decoders.dzen import Dzen
from anicli_api.decoders.kodik import Kodik
from anicli_api.decoders.okru import OkRu
from anicli_api.decoders.sibnet import Sibnet
from anicli_api.decoders.vkcom import VkCom
from anicli_api.decoders.yt_dlp_decoder import YtDlpAdapter

ALL_DECODERS = [Kodik, Aniboom, Sibnet, CsstOnline, VkCom, Dzen, OkRu, AnimeJoyDecoder]
