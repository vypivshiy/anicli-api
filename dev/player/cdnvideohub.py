from ssc_codegen import D, ItemSchema


# <div class="player-cvh">
# <video-player
#             id="pcvh"
#             data-title-id="60254"  // id=
#             data-publisher-id="746"  // pub=746
#             ident="cvh"
#             data-aggregator="mali"  // aggr=
#             is-show-voice-only="true"
#             is-show-banner="true"
#                                     episode="1"
#                         priority-voice="Dream Cast"
#     ></video-player>
class PageAnimegoIframe(ItemSchema):
    """A parser for extracting parameters for the cdnvideohub API.

    used in animego

    USAGE:

        - data_title_id for 'id=' param
        - data_publisher_id for 'pub=' param
        - data_aggregator for 'aggr=' param

    GET https://plapi.cdnvideohub.com/api/v1/player/sv/playlist?pub={data_publisher_id}&aggr={data_aggregator}&id={id}

    EXAMPLE:

        GET https://animego.me/cdn-iframe/60254/Dream%20Cast/1/1
        Referer: https://animego.me
    """

    id = D().css(".player-cvh > video-player::attr(id)")
    data_title_id = D().css(".player-cvh > video-player::attr(data-title-id)")
    data_publisher_id = D().css(".player-cvh > video-player::attr(data-publisher-id)")
    ident = D().css(".player-cvh > video-player::attr(ident)")
    data_aggregator = D().css(".player-cvh > video-player::attr(data-aggregator)")
    is_show_voice_only = D(False).css(".player-cvh > video-player::attr(is-show-voice-only)").is_equal("true").to_bool()
    is_show_banner = D(False).css(".player-cvh > video-player::attr(id)").is_equal("true").to_bool()
    episode = D().css(".player-cvh > video-player::attr(episode)").to_int()
    priority_voice = D().css(".player-cvh > video-player::attr(priority-voice)")


class PageParseCdnVideoData(ItemSchema):
    """universal extractor cdnvideohub API params

    page should be contains <video-player> tag
    """

    id = D().css("video-player::attr(id)")
    data_title_id = D().css("video-player::attr(data-title-id)")
    data_publisher_id = D().css("video-player::attr(data-publisher-id)")
    ident = D().css("video-player::attr(ident)")
    data_aggregator = D().css("video-player::attr(data-aggregator)")
