"""universal parser for kodik.info/serial entrypoint"""

from ssc_codegen import ItemSchema, ListSchema, DictSchema, D, N, R, Json


class UrlParams(Json):
    d: str
    d_sign: str
    pd: str
    pd_sign: str
    ref: str
    ref_sign: str
    advert_debug: bool
    min_age: int
    first_url: bool


class KodikAPIPayload(ItemSchema):
    """payload for Kodik API request"""

    # single params pairs
    d = R().re(r"var\s*domain\s+=\s+['\"](.*?)['\"];")
    d_sign = R().re(r"var\s*d_sign\s+=\s+['\"](.*?)['\"];")
    pd = R().re(r"var\s*pd\s+=\s+['\"](.*?)['\"];")
    pd_sign = R().re(r"var\s*pd_sign\s+=\s+['\"](.*?)['\"];")
    ref = R().re(r"var\s*ref\s+=\s+['\"](.*?)['\"];")
    ref_sign = R().re(r"var\s*ref_sign\s+=\s+['\"](.*?)['\"];")
    type = R().re(r"videoInfo\.type\s*=\s*['\"](.*?)['\"];")
    hash = R().re(r"videoInfo\.hash\s*=\s*['\"](.*?)['\"];")
    id = R().re(r"videoInfo\.id\s*=\s*['\"](.*?)['\"];")


class PageMainKodikMin(ItemSchema):
    """Universal parser for extract minimal data for next API reuqest

    For extract full detailed information (about attached playlists) use:

    - MainKodikSerialPage for serials, OVA
    - MainKodikVideoPage for films

    USAGE:

        1. GET <kodik-page-player>
        2. add base_url to <player_js_path>
        3. extract API (<API_PATH>) path from javascript file (use MainKodikAPIPath)
        3.1 decode <API_PATH> path (base64 cipher)
        4. <api_payload> required extra constant keys
            - bad_user = (true or false)
            - cdn_is_working = true
            - info "{}"
        4.1 required headers:
            - origin="https://<NETLOC>" // player page
            - referer=<PLAYER_LINK> // FIRST URL player entrypoint
            - accept= "application/json, text/javascript, */*; q=0.01"
        4.2 POST <kodik-base-url> + /<API_PATH>
           data=<api_payload> (<JSON>) + headers
        5. extract urls from ['links'] key
        6. video urls encoded in ROT_13 + BASE64 ciphers

    EXAMPLE:

        - GET https://kodik.info/serial/64218/890744b309ec026d43742995d0d49cd7/720p?season=1&episode=1
        - GET https://aniqit.com/video/72755/dc966c03a7cb719dac577d8004a9b091/720p
        - GET https://kodik.info/seria/1133512/04d5f7824ba3563bd78e44a22451bb45/720p

     ISSUES:

        - kodik maybe have another netloc (e.g.: anivod)
        - 403 Forbidden if request sent not from CIS region
        - 404 DELETED: eg: https://kodik.info/seria/310427/09985563d891b56b1e9b01142ae11872/720p
        - 500 Internal server error: eg: https://kodik.info/seria/1051016/af405efc5e061f5ac344d4811de3bc16/720p ('Cyberpunk: Edgerunners' ep5 Anilibria dub)

    """

    url_params = R().re(r"var\s*urlParams\s*=\s*['\"](\{.*\})['\"]").jsonify(UrlParams)
    api_payload = N().sub_parser(KodikAPIPayload)
    # required for extract valid player API path
    player_js_path = D().css('head > script[type="text/javascript"][src*="assets/js"]::attr(src)')


class SeasonBox(ListSchema):
    """represent season select"""

    # <option value="1" data-serial-id="56718" data-serial-hash="710546f4fc603bdd8c41a7e790a2828c"
    # data-title="1 СЃРµР·РѕРЅ" selected="selected"
    # data-other-translation="false" data-translation-title="РљРћРњРќРђРўРђ Р”РР”Р">1 СЃРµР·РѕРЅ</option>
    __SPLIT_DOC__ = D().css_all(".serial-panel > .serial-seasons-box option")

    value = D().attr("value")
    data_serial_id = D().attr("data-serial-id")
    data_serial_hash = D().attr("data-serial-hash")
    data_title = D().attr("data-title")
    data_translation_title = D().attr("data-translation-title")


class SeriesBox(ListSchema):
    """represent selected series in current page"""

    # <option value="1" data-id="1258425" data-hash="3b688251930a4ebb3821be95d9a30362"
    # data-title="1 СЃРµСЂРёСЏ" data-other-translation="false">1 СЃРµСЂРёСЏ</option>
    __SPLIT_DOC__ = D().css_all(".serial-panel > .serial-series-box option")

    value = D().attr("value")
    data_id = D().attr("data-id")
    data_hash = D().attr("data-hash")
    data_title = D().attr("data-title")


class SeriesOptionItem(ListSchema):
    #  <option value="1" data-id="1258425"
    #  data-hash="3b688251930a4ebb3821be95d9a30362"
    #  data-title="1 СЃРµСЂРёСЏ" data-other-translation="false">1 СЃРµСЂРёСЏ
    #  </option>
    __SPLIT_DOC__ = D().css_all("option")

    value = D().attr("value")
    data_id = D().attr("data-id")
    data_hash = D().attr("data-hash")
    data_title = D().attr("data-title")


class SeriesOptions(DictSchema):
    # <div class="series-options">
    #           <div class="season-1">
    #               <option value="1" data-id="1258425"
    #               data-hash="3b688251930a4ebb3821be95d9a30362"
    #               data-title="1 СЃРµСЂРёСЏ" data-other-translation="false">1 СЃРµСЂРёСЏ</option>
    # ...
    __SPLIT_DOC__ = D().css_all(".serial-panel > .series-options div")

    __KEY__ = D().attr("class")
    __VALUE__ = N().sub_parser(SeriesOptionItem)


class TranslationsBox(ListSchema):
    __SPLIT_DOC__ = D().css_all(".serial-panel > .serial-translations-box option")
    # <option value="2822" data-id="2822" data-translation-type="voice" data-media-id="56791"
    # data-media-hash="c1adc4138bed1a558fee47f70403788a" data-media-type="serial"
    # data-title="AniBaza" data-episode-count="12">AniBaza (12 СЌРї.)</option>
    value = D().attr("value")
    data_id = D().attr("data-id")
    data_translation_type = D().attr("data-translation-type")
    data_media_id = D().attr("data-media-id")
    data_media_hash = D().attr("data-media-hash")
    data_media_type = D().attr("data-media-type")
    data_title = D().attr("data-title")
    # one-peace contains this value in "1~1122" format
    # fix it for avoid convert type issues
    data_episode_count = D().attr("data-episode-count").re(r"(\d+)$")


class PageMainKodikSerial(PageMainKodikMin):
    """First extract data entrypoint for kodik.../serial/ entrypoint path


    EXAMPLE:
        GET - https://kodik.info/serial/64218/890744b309ec026d43742995d0d49cd7/720p?season=1&episode=1

    """

    thumbnails = R().re(r"var\s*thumbnails\s*=\s*\[(.*?)\];").repl('"', "").split(",").trim().fmt("https:{{}}")
    season_box = N().sub_parser(SeasonBox)
    series_box = N().sub_parser(SeriesBox)
    series_options = N().sub_parser(SeriesOptions)
    translations_box = N().sub_parser(TranslationsBox)


class MovieTranslationBox(ListSchema):
    """PageMainKodikVideo /video/ (film) segment"""

    #  <option
    #                 value="1060"
    #                 data-id="1060"
    #                 data-translation-type="voice"
    #                 data-media-id="96215"
    #                 data-media-hash="e4b73601a7b886679e1625172689bcf9"
    #                 data-media-type="video"
    #                 data-title="MiraiDUB"
    #               >MiraiDUB</option>
    __SPLIT_DOC__ = D().css_all(".movie-panel > .movie-translations-box option")

    value = D().attr("value")
    data_id = D().attr("data-id")
    data_translation_type = D().attr("data-translation-type")
    data_media_id = D().attr("data-media-id")
    data_media_hash = D().attr("data-media-hash")
    data_media_type = D().attr("data-media-type")
    data_title = D().attr("data-title")


class PageMainKodikVideo(PageMainKodikMin):
    """First extract data entrypoint for kodik.../video/ entrypoint path (FILMS, less often OVA)

    required for extract videos via kodik API

    EXAMPLE:

        - GET https://kodik.info/video/9935/313bc89421b094f6f374cc7420e00ad1/720p?translations=false&min_age=16 (Кланнад фильм)
        - GET https://kodik.info/video/72755/dc966c03a7cb719dac577d8004a9b091/720p?translations=false&min_age=16 (Вайолет Эвергарден. Фильм)
    """

    # url_params = R().re("var\s*urlParams\s*=\s*['\"](\{.*\})['\"]").jsonify(UrlParams)
    # api_payload = N().sub_parser(KodikAPIPayload)
    # # required for extract valid player API path
    # # app.player_single...js or app.player...js
    # player_js_path = R().re('<script\s*type="text/javascript"\s*src="(/assets/js/app\..*?)">')

    thumbnails = R().re(r"var\s*thumbnails\s*=\s*\[(.*?)\];").repl('"', "").split(",").trim().fmt("https:{{}}")
    translation_box = N().sub_parser(MovieTranslationBox)


class PageMainKodikAPIPath(ItemSchema):
    """Extract actual API path from kodik player javascript sources

    after parse, required base64 decode string

    USAGE:
        GET MainKodikPage.player_js_path, MainKodikSerialPage.player_js_path

    EXAMPLE:

        - GET https://kodik.info/assets/js/app.serial.6721f2dd68501a625a518ea935006bd8f5cf5f4d037f2648a97a02dfd0fe5b85.js
        - GET https://aniqit.com/assets/js/app.player_single.3e2f9f0ae45d18b06cfd8b01181f85bab47fb9867cd1e73568c84dbe44ba7a44.js

    """

    # WARNING: correct translate code broken, use direct extract path via regexp

    # js api path signature examples:
    # ... $.ajax({type:"POST",url:atob("L2Z0b3I="),cache:! ...
    # ... $.ajax({type: 'POST', url:atob('L3RyaQ=='),cache: !...
    api_path = R().re(r"\$\.ajax[^)]+atob\([\"\'](\w+=)[\'\"]\)")
