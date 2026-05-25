from anicli_api.player.aniboom import Aniboom
from anicli_api.player.aksor import Aksor
from anicli_api.player.csst import CsstOnline
from anicli_api.player.kodik import Kodik
from anicli_api.player.sibnet import SibNet
from anicli_api.player.sovetromantica import SovietRomanticaPlayer
from anicli_api.player.sovetromantica_embed import SovietRomanticaEmbed
from anicli_api.player.cdnvideohub import CdnVideoHub, video_playlist_from_vk_id, a_video_playlist_from_vk_id # type: ignore

ALL_DECODERS = (Kodik, Aniboom, Aksor, SibNet, CsstOnline, SovietRomanticaPlayer, SovietRomanticaEmbed, CdnVideoHub)

