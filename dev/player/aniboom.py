from ssc_codegen import D, ItemSchema, Json


class Dash(Json):
    src: str
    type: str


class Hls(Json):
    src: str
    type: str


class DataParameters(Json):
    id: str
    error: str
    domain: str
    cdn: str
    counter: str
    duration: str
    poster: str
    thumbnails: str
    dash: Dash
    hls: Hls
    quality: bool
    qualityVideo: int
    vast: bool
    country: str
    platform: str
    rating: str
    nshowbl: bool
    limitRate: bool
    aBlocklimitRate: bool


class PageAniboom(ItemSchema):
    """Extract MPD and M3U8 urls

    NOTE: use data_parameters instead hls and dash keys for get urls

    Required `referer="https://animego.org/` HEADER (.me, .club?)

    USAGE:
        1. GET <PLAYER_LINK> (e.g. https://aniboom.one/embed/6BmMbB7MxWO?episode=1&translation=30)
        2. PARSE. If pre-unescape response before parse - css selector may not find attribute
        3. For video playing, url required next headers:

        - Referer="https://aniboom.one/"
        - Accept-Language="ru-RU"  # INCREASE DOWNLOAD SPEED with this static value
        - Origin="https://aniboom.one"
    ISSUES:
        - 403 Forbidden if request sent not from CIS region
        - KEYS SHOULD BE STARTED IN Title Case else hls/mpd links returns 403 error
        - Sometimes, aniboom backend missing MPD key and returns M3U8 url. Check this value before usage:

        https://github.com/vypivshiy/ani-cli-ru/issues/29

        Expected json signature (LOOK at dash.src and hls.src keys):

        { ...
        "dash":"{\"src\":\"https:.../abcdef.mpd\",\
        "type\":\"application\\\/dash+xml\"}",
        "hls":"{\"src\":\"https:...\\\/master_device.m3u8\",
        \"type\":\"application\\\/x-mpegURL\"}"

        ... }

        MAYBE returns this:

         { ...
        "dash":"{\"src\":\"https:...master_device.m3u8\",\
        "type\":\"application\\\/dash+xml\"}",
        "hls":"{\"src\":\"https:...master_device.m3u8\",
        \"type\":\"application\\\/x-mpegURL\"}"

        ... }
    """

    data_parameters = (
        D()
        .css("#video[data-parameters]")
        .attr("data-parameters")
        # unescape json
        .repl("\\", "")
        .repl("&quot;}", "}")
        .repl("&quot;{", "{")
        .repl("&quot;", '"')
        # if backend parser try automatically unquote raw json
        # fix it
        .repl('}"', "}")
        .repl('"{', "{")
    ).jsonify(DataParameters)

    # backport for old API impl realizations
    hls = (
        D()
        .css("#video")
        .attr("data-parameters")
        .repl("\\", "")
        .repl("&quot;", '"')
        .re(r'"hls":"{"src":"(https?.*?\.m3u8)"')
    )

    dash = (
        D()
        .css("#video[data-parameters]")
        .attr("data-parameters")
        .repl("\\", "")
        .repl("&quot;", '"')
        .re(r'"dash":"{"src":"(https?.*?\.(?:mpd|m3u8))"')
    )
