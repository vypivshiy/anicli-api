"""Thanks https://github.com/barsikus007 for researches and decoder impl

NOTE: for extract Search and Ongoing items use rest-api requests

Ongoing:
        POST https://dreamerscast.com/"
        {'search': "", "status": "", "pageSize": 16, 'pageNumber': 1}

Search:

    POST https://dreamerscast.com/"
    {'search': "<QUERY>", "status": "", "pageSize": 16, 'pageNumber': 1}


For extract playlist required reverse obfuscated playlist data and obfuscated javascript player
"""

from ssc_codegen import D, R, ItemSchema


FMT_URL = "https://dreamerscast.com" + "{{}}"


class PageAnime(ItemSchema):
    """
    Usage example:

    GET https://dreamerscast.com/home/release/323-tensei-kizoku-kantei-skill-de-nariagaru-2

    Encoding (24.12.24 actual step-by-step)

    decoding and extract playlist:

    - GET <player_js_url>
    - unpack, extract encoded symbols
    - by <player_js_encoded> and <player_js_url> values decrypt it (implement logic from original player sources)
    """

    title = D().css("h3::text")
    description = D(None).css(".postDesc::text")
    thumbnail = D().css(".details_poster img::attr(src)").fmt("https:{{}}")

    # opfuscated playlist
    player_js_encoded = R().re(r'new Playerjs\("(.*?)"\)')
    # obfuscated javscript file (required for decode `player_js_encoded`)
    player_js_url = R().re(r'<script[^>]+src="(/js/playerjs.*?)"').fmt(FMT_URL)
