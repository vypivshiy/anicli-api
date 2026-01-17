from ssc_codegen import D, N, DictSchema, ItemSchema, ListSchema, Json


class PageUtils(ItemSchema):
    # old domain - animego.org
    # this provider can be replace domains by redirect
    # helper function page for fix ongoings url
    url_canonical = D().css('link[rel="canonical"]::attr(href)').rtrim("/")


class PageOngoing(ListSchema):
    """Get all available ongoings from the main page

    GET https://animego.one


    NOTE: animego can change the domain, so only the path is returned.
    To get the real url, extract the value using the selector 'link[rel="canonical"]::attr(href)'

    """

    # old domain - animego.org
    # can be replace domains by redirect

    __SPLIT_DOC__ = D().css_all(".updates-body > div.d-grid > a.aw-item")

    url_path = D().attr("href")
    title = D().css(".image__img::attr(alt)")
    thumbnail = D().css(".image__img::attr(src)")
    # first num - episode counter
    # eg signature:
    """ Серия 2 · Субтитры — Сегодня, 21:50
                                                            
    """
    episode = D().css(".aw-meta::text").re(r"\s(\d+)\s")
    dub = D().css(".aw-meta::text").re(r"(\w+)\s+—")


class PageSearch(ListSchema):
    """Get all search results by query

    USAGE:

        GET https://animego.one/search/anime
        q={QUERY}

    EXAMPLE:

        GET https://animego.one/search/anime?q=LAIN
    """

    __SPLIT_DOC__ = D().css_all(".grid.ani-list .ani-grid__item")

    title = D().css("a.ani-grid__item-picture img::attr(alt)")
    thumbnail = D().css(".image__img::attr(src)")
    # todo: extract path instead use hardcoded full url
    url = D().css(".ani-grid__item-title a::attr(href)").fmt("https://animego.me{{}}")


# Anime page content
###
class AggregateRating(Json):
    type: str
    ratingCount: int
    bestRating: int
    ratingValue: str


class Director(Json):
    type: str
    url: str
    name: str


class Actor(Json):
    type: str
    url: str
    name: str


class Creator(Json):
    type: str
    name: str


class Content(Json):
    context: str
    type: str
    url: str
    name: str
    alternateName: str
    image: str
    description: str
    genre: list[str]
    contentRating: str
    datePublished: str
    keywords: str
    creator: list[Creator]
    aggregateRating: AggregateRating
    numberOfEpisodes: int


class PageAnime(ItemSchema):
    """Anime page information. anime path contains in SearchView.url or Ongoing.url

    - id needed for next API requests
    - raw_json used for extract extra metadata (unescape required)

    USAGE:

        GET https://animego.one/anime/<ANIME_PATH>

    EXAMPLE:

        GET https://animego.one/anime/eksperimenty-leyn-1114


    ISSUES:
        If blocked, you can try skip extract anime metadata and send api request:

        id contains in url:
            - id=1114 for https://animego.one/anime/eksperimenty-leyn-1114
            - id=2589 for https://animego.org/anime/chelovek-muskul-2589

        GET 'https://animego.one/anime/{id}/player?_allow=true'
    """

    title = D().css(".entity__title h1::text")
    # maybe missing description eg:
    # https://animego.org/anime/chelovek-muskul-2589
    description = D("").css_all(".description::text").join("").re_trim()
    thumbnail = D().css(".d-sm-flex .image__picture img.image__img::attr(src)")
    # anime id required for next requests (for DubberView, Source schemas)
    id = D().css('link[rel="canonical"]::attr(href)').re(r"-(.?\d{2,})")

    # DEV key: for parse extra metadata can be json unmarshal.
    # unescape required
    raw_json = (
        D()
        .css("script[type='application/ld+json']")
        .text()
        # patch keys for success generating key
        .repl('"@type"', '"type"')
        .repl('"@context"', '"context"')
    ).jsonify(Content)


class Episodes(ListSchema):
    """episodes signature example (exclude in film)
    ```
    <div class="scroll-snap-slider d-none d-lg-flex">
        <div class="scroll-snap-slide player-video-bar__item user-select-none px-1"
            data-episode-number="1" data-episode-type="1"
            data-episode-title="Elaina, the Apprentice Witch" data-episode-released="2 октября 2020"
            data-episode-description="" data-episode="21516">
            ...
    ```
    """

    __SPLIT_DOC__ = D().css_all(".player-video-bar__item")

    num = D().attr("data-episode-number").re_sub(r"[^\d+]").to_int()
    title = D().attr("data-episode-title")
    type = D().attr("data-episode-type")
    released = D().attr("data-episode-released")
    id = D().attr("data-episode")


class Dubbers(DictSchema):
    """dubbers signature:

    ```
    <div class="list-group pt-2 position-absolute w-100">
        <button class="align-items-center d-flex gap-2 list-group-item list-group-item-action mb-1"
                role="button" data-translation="2"><span class="text-truncate">AniLibria</span> <span
                class="error__player d-none text-danger small text-nowrap">(ошибка)</span>
        </button>
    ...
    ```

    """

    __SPLIT_DOC__ = D().css_all("button[data-translation]")

    __KEY__ = D().attr("data-translation")
    __VALUE__ = D().css("span").text().trim()


class PageEpisode(ItemSchema):
    """Representation episodes

    NOTE:
        film pages does not exist select[name="series"] element.

    Prepare:
      1. get id from Anime object
      2. GET 'https://animego.me/player/{Anime.id}'
      3. extract html from json by ['data']['content'] key
      4. OPTIONAL: unescape HTML

    EXAMPLE:
        GET https://animego.me/player/1114
    """

    is_film = D(True).is_not_css('select[name="series"]').to_bool()

    episodes = N().sub_parser(Episodes)
    dubbers = N().sub_parser(Dubbers)


class EpisodeVideos(ListSchema):
    """

    signature:

    ```
     <button data-player="//aniboom.one/embed/z68qn1VdNvg?translation=2" data-provider="24"
            data-ptranslation="2" data-provider-title="AniBoom" data-translation-title="AniLibria"
            class="align-items-center d-flex gap-2 list-group-item list-group-item-action mb-1"
            role="button"><span class="text-truncate">AniBoom</span> <span
                class="error__player d-none text-danger small text-nowrap">(ошибка)</span></button>

    ...
    ```

    """

    __SPLIT_DOC__ = D().css_all("button[data-player]")
    # '//kodik.info/...'
    player = D().attr("data-player").re_sub("^https?", "").fmt("https:{{}}")
    data_provider = D().attr("data-provider")
    data_provide_dubbing = D().attr("data-ptranslation").re_trim()


class PageEpisodeVideo(ItemSchema):
    """Represent Episode object for film (it have not same signatures)

    NOTE:
        film pages does not exist CSS selector `.player-video-bar__item` or `select[name="series"]`

    Prepare:
      1. get id from Anime object
      2. GET 'https://animego.one/player/{Anime.id}'
      3. extract html from json by ['data']['content'] key
      4. OPTIONAL: unescape HTML

    EXAMPLE:
        GET https://animego.one/player/315
    """

    is_film = D(True).is_not_css('select[name="series"]').to_bool()

    dubbers = N().sub_parser(Dubbers)
    videos = N().sub_parser(EpisodeVideos)


class SourceVideoView(ListSchema):
    """Signature:

    ```
     <button data-player="//animego.me/cdn-iframe/40571/AnilibriaTV/1/2" data-provider="26"
            data-ptranslation="2" data-provider-title="CVH" data-translation-title="AniLibria"
            class="align-items-center d-flex gap-2 list-group-item list-group-item-action mb-1"
            role="button"><span class="text-truncate">CVH</span> <span
                class="error__player d-none text-danger small text-nowrap">(ошибка)</span></button>
    ```

    """

    __SPLIT_DOC__ = D().css_all("button[data-player]")

    title = D().css("span").text()
    url = D().attr("data-player").fmt("https:{{}}")
    data_provider = D().attr("data-provider")
    data_provide_dubbing = D().attr("data-ptranslation")
    data_translation_title = D().attr("data-translation-title")


class PageSource(ItemSchema):
    """representation player urls (episodes only)

    Prepare:
      1. get num and id from Episode

      2.

      GET https://animego.me/player/videos/{Episode.id}

      3. extract html from json by ["data"]["content"] key

      4. OPTIONAL: unescape document

    EXAMPLE:

        GET https://animego.one/anime/series?dubbing=2&provider=24&episode=2&id=15837
    """

    dubbers = N().sub_parser(Dubbers)
    videos = N().sub_parser(SourceVideoView)
