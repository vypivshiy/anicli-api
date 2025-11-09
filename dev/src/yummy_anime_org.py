from ssc_codegen import ItemSchema, D, ListSchema


class PageUtils(ItemSchema):
    """extract canonical url"""

    # HACK: get url from rss tag
    url = D().css('link[rel="canonical"], link[rel="alternate"] ::attr(href)').rtrim("/").rm_suffix("/rss.xml")


class PageOngoing(ListSchema):
    """Get all available ongoings from the main page

    can be change domains, extract real domain from `link[rel="canonical"]` element
    USAGE:

        GET https://yummyanime.in/

    """

    __SPLIT_DOC__ = D().css_all(".ksupdate_block a")

    thumbnail_path = D().css(".xfieldimage[src]::attr(src)")
    url_path = D().attr("href")
    # maybe not exist episode number in element, set 1 as default
    episode = D().default(1).css(".cell-2").text().re(r"(\d+)\s").to_int()
    title = D().css(".xfieldimage[alt]::attr(alt)")


class PageSearch(ListSchema):
    """Get search results

    USAGE:

        POST https://yummyanime.in
        do=search&subaction=search&story=<QUERY>

    EXAMPLE:

        POST https://yummyanime.in/index.php
        do=search&subaction=search=from_page=0story=ван-пис
    """

    __SPLIT_DOC__ = D().css_all("a.has-overlay")

    title = D().css(".poster__title::text")
    thumbnail_path = D().css(".xfieldimage[data-src]::attr(data-src)")
    url = D().attr("href")


class PageAnime(ItemSchema):
    """get anime page

    USAGE:

        GET https://yummyanime.in/<...>.html

    EXAMPLE:

        GET https://yummyanime.in/4790-vedma-i-chudovische.html

    """

    title = D().css(".anime__title h1::text")
    alt_title = D(None).css(".anime__title .pmovie__original-title::text")

    description = D("").css_all(".page__text p::text").join("")
    thumbnail = D().css(".pmovie__poster .xfieldimage[data-src]::attr(data-src)")

    # not actual, current site migrate to cdnvideohub host
    # player_url = D(None).css('.pmovie__player iframe[src]::attr(src)').fmt('https:{{}}')
