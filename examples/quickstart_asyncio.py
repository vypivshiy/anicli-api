import asyncio

from anicli_api.extractors import animego


async def step_by_step_search():
    """simple usage api search example"""
    # init extractor
    extractor = animego.Extractor()
    # search by string query
    search = await extractor.async_search("lain")
    print(search[0].dict())  # dict method return all keys
    # step-by-step get objects
    anime = await search[0].a_get_anime()
    episodes = await anime.a_get_episodes()
    videos = await episodes[0].a_get_videos()
    links = await videos[0].a_get_source()
    # get first direct links dict
    print(links)


async def step_by_step_ongoing():
    """simple usage api ongoing example"""

    extractor = animego.Extractor()
    # get all available ongoings
    ongoings = await extractor.async_ongoing()
    ongoing = ongoings[0]
    anime = await ongoing.a_get_anime()
    episodes = await anime.a_get_episodes()
    videos = await episodes[0].a_get_videos()
    links = await videos[0].a_get_source()
    print(links)


async def walk_search():
    """simple usage api async_walk_search example"""
    extractor = animego.Extractor()
    # method return all raw data
    async for meta in extractor.async_walk_search("school"):
        print(meta)


async def walk_ongoing():
    """simple usage api async_walk_ongoing example"""
    extractor = animego.Extractor()
    # method return all raw data
    # TODO implements check duplicates url
    async for meta in extractor.async_walk_ongoing()[:3]:
        print(meta)


async def example_iter_objects():
    extractor = animego.Extractor()
    search = (await extractor.async_search("lain"))[0]
    ongoing = (await extractor.async_ongoing())[0]
    # return raw dict all metadata
    async for meta in search:
        print(meta)

    # return raw dict all metadata
    async for meta in ongoing:
        print(meta)

    anime = await search.a_get_anime()
    # iter search objects
    async for episode in anime:
        async for video in episode:
            print(video.get_source())

    # iter ongoing objects
    anime_ongoing = await ongoing.a_get_anime()
    async for episode in anime_ongoing:
        async for video in episode:
            print(video.get_source())


async def main():
    await step_by_step_search()
    await step_by_step_ongoing()
    await walk_search()
    await walk_ongoing()
    await example_iter_objects()


if __name__ == '__main__':
    asyncio.run(main())
