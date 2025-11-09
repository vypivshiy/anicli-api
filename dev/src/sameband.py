from ssc_codegen import D, ItemSchema, ListSchema, R


class PageOngoing(ListSchema):
    """GET https://sameband.studio/novinki"""

    __SPLIT_DOC__ = D().css_all(".col-auto")

    url = D().css("a[href]::attr(href)")
    title = D().css(".col-auto .poster[title]::attr(title)")
    thumbnail = D().css("img.swiper-lazy[src]::attr(src)").fmt("https://sameband.studio{{}}")


class PageSearch(ListSchema):
    """
    POST https://sameband.studio/index.php?do=search
    do=search&subaction=search&search_start=0&full_search=0&result_from=1&story=<QUERY>

    NOTE:
        search query len should be 4 or more characters. And in manual tests, works only cyrillic queries

    EXAMPLE:
        POST https://sameband.studio/index.php?do=search
    do=search&subaction=search&search_start=0&full_search=0&result_from=1&story=ВЕДЬ
    """

    __SPLIT_DOC__ = D().css_all(".col-auto")

    title = D().css(".col-auto .poster[title]::attr(title)")
    thumbnail = D().css("img.swiper-lazy[src]::attr(src)").fmt("https://sameband.studio{{}}")
    url = D().css(".image[href]::attr(href)")


class PageAnime(ItemSchema):
    """
    GET https://sameband.studio/anime/<ANIME PATH>.html

    EXAMPLE:
        # https://sameband.studio/anime/20-госпожа-кагуя-3.html
        GET https://sameband.studio/anime/20-%D0%B3%D0%BE%D1%81%D0%BF%D0%BE%D0%B6%D0%B0-%D0%BA%D0%B0%D0%B3%D1%83%D1%8F-3.html
    """

    title = D().css("h1.m-0::text")
    alt_title = D().css(".help::text").re_trim()
    description = D().css_all(".limiter span::text").join(" ")
    thumbnail = D().css(".image > img[src]::attr(src)").fmt("https://sameband.studio{{}}")
    # url for access playlist
    #
    #  tag signature:
    #
    # <body>
    #     <div id="player"></div>
    #  <script>var player = new Playerjs({id:"player",file:"/v/list/....txt"});
    # </script>
    # </body>
    player_url = D().css(".player > .player-content > iframe[src]::attr(src)").fmt("https://sameband.studio{{}}")


class PagePlaylistURL(ItemSchema):
    """GET https://sameband.studio/pl/a/<PLAYLIST NAME>.html

    EXAMPLE:
        GET https://sameband.studio/pl/a/Mashle_2nd_Season.html


    url contains in AnimeView.player_url key:

      playlist items signature (need manually provide json unmarshall logic):

    ```
        [
            {
                "title": "<img src='/v/anime/...01 RUS_snapshot.jpg' class=playlist_poster><div class=playlist_duration>23:37</div>... 01",
                ### delimiter - ','
                "file": "[480p]/v/anime/... - 01 RUS_480p/... - 01 RUS_r480p.m3u8,[720p]/v/anime/.../... - 01 RUS_720p/... - 01 RUS_r720p.m3u8,[1080p]/v/anime/.../... -
                01 RUS_1080p/... - 01 RUS_r1080p.m3u8",
                ### thumbnails images for video
                "thumbnails": "/v/anime/.../thumbnails/... - 01 RUS.txt"  # contains
            },
            {
                ...
            },
            ...
        ]
    ```
    player script signature:
    ...
    <script>var player = new Playerjs({id:"player",file:"/v/list/....txt"});
    ...
    """

    playlist_url = R().re(r"Playerjs[^>]+file:\s*[\"']([^>]+)[\"']").fmt("https://sameband.studio{{}}")
    # note: urlpath maybe contains whitespace instead `_` char in, fix it^^^^^^
