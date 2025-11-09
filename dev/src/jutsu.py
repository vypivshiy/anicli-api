from ssc_codegen import D, N, DictSchema, ItemSchema, ListSchema


class PageOngoing(ListSchema):
    """usage:

    POST https://jut.su/anime/ongoing/
    ajax_load=yes&start_from_page=1&show_search=&anime_of_user=

    """

    __SPLIT_DOC__ = D().css_all(".all_anime_global")

    url = D().css("a::attr(href)").fmt("https://jut.su{{}}")
    title = D().css(".aaname::text")
    # background: url('https://gen.jut.su/uploads/animethumbs/aaaa.jpg')  no-repeat;
    thumbnail = D().css(".all_anime_image[style]::attr(style)").re("'(https?://.*?)'")
    # <div class="aailines">
    #         1094 серии
    #         <br>
    #         14 фильмов
    # </div>
    counts = D().css_all(".aailines::text").trim("\r\n ").join(" ")


class PageSearch(PageOngoing):
    """
    POST https://jut.su/anime/
    ajax_load=yes&start_from_page=1&show_search=<QUERY>&anime_of_user=

    EXAMPLE:
        POST https://jut.su/anime/
        ajax_load=yes&start_from_page=1&show_search=LA&anime_of_user=
    """

    pass


class EpisodesView(ListSchema):
    __SPLIT_DOC__ = D().css_all(".video")

    title = D().text().trim(" ")
    url = D().attr("href").fmt("https://jut.su{{}}")


class PageAnime(ItemSchema):
    """
    GET https://jut.su/<ANIME PATH>

    EXAMPLE:
        GET https://jut.su/kime-no-yaiba/
    """

    # test cases:
    # Смотреть Клинок, рассекающий демонов все серии и сезоны
    # Смотреть ТораДора все серии
    title = D().css(".anime_padding_for_title::text").re(r"Смотреть\s*(.*?)\s*все")
    description = D().css_all(".uv_rounded_bottom span::text").join(" ")
    # background: url('https://gen.jut.su/uploads/animethumbs/anime_toradora.jpg') no-repeat; background-size: 104px auto;
    thumbnail = D().css(".all_anime_title[style]::attr(style)").re("'(https?://.*?)'")
    episodes = N().sub_parser(EpisodesView)


class SourceView(DictSchema):
    __SPLIT_DOC__ = D().css_all("#my-player > source")
    __SIGNATURE__ = {"QUALITY": "URL"}

    __KEY__ = D("null").attr("res")  # ssc-gen limitations: only supports string type
    __VALUE__ = D(None).attr("src")


class PageSource(ItemSchema):
    """
    GET https://jut.su/<ANIME PATH>/<SEASON?>/episode-<NUM>.html

    NOTE: VIDEO PLAY REQUEST SHOULD HAVE THE SAME USER-AGENT AS AN API CLIENT

    eg:

    cl = Client(headers={"user-agent": "X"})

    ...

    s = SourcePage(doc).parse()

    mpv s["url_1080"] # 403, FORBIDDEN

    mpv s["url_1080"] --user-agent="Y" # 403, FORBIDDEN

    mpv s["url_1080"] --user-agent="X" # 200, OK

    EXAMPLE:
        GET https://jut.su/kime-no-yaiba/season-1/episode-1.html

    ISSUES:
        CHECK 'null' KEY in 'video'. if it contains - videos not available

        check block reasons regex patterns:

        - 'block_video_text_str_everywhere\\\+' - К сожалению, это видео недоступно.
        - 'block_video_text_str\\\+' - К сожалению, в России это видео недоступно.
    """

    videos = N().sub_parser(SourceView)
