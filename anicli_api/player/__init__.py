from anicli_api.player.aniboom import Aniboom
from anicli_api.player.animejoy import AnimeJoy
from anicli_api.player.csst import CsstOnline
from anicli_api.player.dzen import Dzen
from anicli_api.player.kodik import Kodik
from anicli_api.player.mailru import MailRu
from anicli_api.player.okru import OkRu
from anicli_api.player.sibnet import SibNet
from anicli_api.player.sovetromantica import SovietRomanticaPlayer
from anicli_api.player.vkcom import VkCom

ALL_DECODERS = (
    Kodik,
    Aniboom,
    SibNet,
    AnimeJoy,
    CsstOnline,
    MailRu,
    OkRu,
    VkCom,
    Dzen,
    SovietRomanticaPlayer,
)
