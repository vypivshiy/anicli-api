from anicli_api.decoders.aniboom import Aniboom
from anicli_api.decoders.base import BaseDecoder, MetaVideo
from anicli_api.decoders.kodik import Kodik
from anicli_api.decoders.sibnet import Sibnet

ALL_DECODERS = (Kodik, Aniboom, Sibnet)
