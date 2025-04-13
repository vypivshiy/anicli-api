"""thanks https://github.com/barsikus007 for researches and decoder implementation"""

import base64
import json
import re
import urllib.parse
from typing import Tuple, List, Dict, Any

NoneType = type(None)  # py3.8 backport type
T_PACKED = Tuple[str, int, int, List[str], NoneType, Dict[str, str]]

# consts from playerjs
_O_Y = "xx???x=xx?x??="  # maybe dynamic
_ABC = "ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz"
_SALT_ABC_STRING = f"{_ABC}0123456789+/="

_RE_O_U1 = re.compile(r"u:\s*\\\s*['\"]([^=]+=[\\]+)\s*['\"]")
"""js script encoded"""

_BASE36_STRING = "0123456789abcdefghijklmnopqrstuvwxyz"

# search anchors
_PARAMS_START = "return p}('"
_PARAMS_PACKED_OFFSET = len(_PARAMS_START) - 1

__all__ = ["extract_playlist"]


def parse_params_to_unpack(packed: str) -> T_PACKED:
    index = packed.find(_PARAMS_START)  # start js code paks

    packed = packed[index + _PARAMS_PACKED_OFFSET : -1]
    p_re = re.search(r"'(.*[^\\])',", packed)
    try:
        p = p_re[1]  # type: ignore
        packed = packed[p_re.span(1)[1] + 2 :]  # type: ignore
        a_re = re.search(r"(\d+),", packed)
        a = int(a_re[1])  # type: ignore
        packed = packed[a_re.span(1)[1] + 1 :]  # type: ignore
        c_re = re.search(r"(\d+),", packed)
        c = int(c_re[1])  # type: ignore
        packed = packed[c_re.span(1)[1] + 1 :]  # type: ignore
        k_re = re.search(r"'(.*)[^\\]'\.split", packed)
        k = k_re[1].split("|")  # type: ignore
    except AttributeError as e:
        raise ValueError("Could not extract params from packed playerjs") from e
    _, d = None, {}  # type: ignore
    return p, a, c, k, _, d


def unpack_playerjs(p: str, a: int, c: int, k: List[str], _: NoneType, d: Dict[str, str]) -> str:
    """Playerjs unpacker"""

    def e(c: int):
        return ("" if c < a else e(c // a)) + (chr(c + 29) if (c := c % a) > 35 else _BASE36_STRING[c])

    while c:
        c -= 1
        d[e(c)] = k[c] or e(c)
    p = re.sub(r"\b\w+\b", lambda e: d.get(e.group(), e.group()), p)

    return p


def get_crypt_codes(playerjs_packed_script):
    packed_params = parse_params_to_unpack(playerjs_packed_script)
    playerjs_script = unpack_playerjs(*packed_params)

    return _RE_O_U1.search(playerjs_script)[1]


# region playerjs crypto
def decode(x):
    if x[:2] == "#1":
        return Salt().d(pepper(x[2:], -1))
    elif x[:2] == "#0":
        return Salt().d(x[2:])
    else:
        return x


class Salt:
    def __init__(self, key_str=_SALT_ABC_STRING):
        self._keyStr = key_str

    def d(self, e):
        t = ""
        f = 0
        e = "".join([c for c in e if c in self._keyStr])
        while f < len(e):
            s = self._keyStr.index(e[f])
            f += 1
            o = self._keyStr.index(e[f])
            f += 1
            u = self._keyStr.index(e[f])
            f += 1
            a = self._keyStr.index(e[f])
            f += 1
            n = (s << 2) | (o >> 4)
            r = ((o & 15) << 4) | (u >> 2)
            i = ((u & 3) << 6) | a
            t += chr(n)
            if u != 64:
                t += chr(r)
            if a != 64:
                t += chr(i)
        return self._ud(t)

    @staticmethod
    def _ud(e):
        t = ""
        n = 0
        while n < len(e):
            r = ord(e[n])
            if r < 128:
                t += chr(r)
                n += 1
            elif 191 < r < 224:
                c2 = ord(e[n + 1])
                t += chr(((r & 31) << 6) | (c2 & 63))
                n += 2
            else:
                c2 = ord(e[n + 1])
                c3 = ord(e[n + 2])
                t += chr(((r & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63))
                n += 3
        return t


def pepper(s, n):
    s = s.replace("+", "#")
    s = s.replace("#", "+")
    a = sugar(_O_Y) * n
    if n < 0:
        a += len(_ABC) / 2
    r = _ABC[int(a * 2) :] + _ABC[: int(a * 2)]
    return re.sub(r"[A-Za-z]", lambda c: r[_ABC.index(c.group())], s)


def sugar(x):
    x = x.split(chr(61))
    result = ""
    c1 = chr(120)
    for item in x:
        encoded = "".join(chr(49) if char == c1 else chr(48) for char in item)
        chr_val = int(encoded, 2) if encoded else 0
        result += chr(chr_val)
    return int(result[:-1])


# endregion playerjs crypto


def b64e_url_params(s):
    return base64.b64encode(urllib.parse.quote(s).encode()).decode()


def b64d_url_params(s):
    return urllib.parse.unquote(base64.b64decode(s).decode())


def extract_playlist(player_js_packed_response: str, player_encoded: str) -> Dict[str, Any]:
    """extract and decode playlist from dreamcast player

    :param player_js_packed_response: raw dreamcast playerjs response
    :param player_encoded: encoded (key? url?) in anime page from $(function() {new Playerjs("(...)")...
    :return: decoded playlist
    """
    o_u = get_crypt_codes(player_js_packed_response)
    v = json.loads(decode(o_u))
    v["file3_separator"] = "//"
    a = player_encoded[2:]
    # bk0 ... bk4 keys
    for key in (f"bk{i}" for i in range(4, -1, -1)):
        if (result := v.get(key)) and result not in ("undefined", "", None):
            a = a.replace(v["file3_separator"] + b64e_url_params(result), "")
    # unsafe, maybe throw error
    return json.loads(b64d_url_params(a))


if __name__ == "__main__":
    import httpx

    from anicli_api.source.parsers.dreamcast_parser import AnimePage

    def main(anime_url: str) -> dict:
        anime_resp = httpx.get(anime_url)
        anime_page = AnimePage(anime_resp.text).parse()
        player_encoded = anime_page["player_js_encoded"]
        player_js_url = anime_page["player_js_url"]

        player_js_packed_response = httpx.get(player_js_url).text
        return extract_playlist(player_js_packed_response, player_encoded)

    print(main("https://dreamerscast.com/home/release/2-vosem-desiat-shest-86-eighty-six"))
    print(main("https://dreamerscast.com/home/release/333-danmachi-5"))
