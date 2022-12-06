import asyncio

from anicli_api.extractors import anilibria


async def step_by_step_search():
    """simple usage api search example"""
    # init extractor
    print("RUN ASYNC STEP BY STEP SEARCH")
    extractor = anilibria.Extractor()
    # search by string query
    search = await extractor.async_search("Мастера меча онлайн")
    print(search[0].dict())  # dict method return all keys
    # step-by-step get objects
    anime = await search[0].a_get_anime()
    episodes = await anime.a_get_episodes()
    videos = await episodes[0].a_get_videos()
    links = await videos[0].a_get_source()
    # get first direct links dict
    print(*links, sep="\n")


async def step_by_step_ongoing():
    """simple usage api ongoing example"""
    print("RUN ASYNC STEP BY STEP ONGOING")
    extractor = anilibria.Extractor()
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
    print("RUN ASYNC WALK SEARCH")
    extractor = anilibria.Extractor()
    # method return all raw data
    async for meta in extractor.async_walk_search("school"):
        print(meta)


async def walk_ongoing():
    """simple usage api async_walk_ongoing example"""
    print("RUN ASYNC WALK ONGOING")
    extractor = anilibria.Extractor()
    # method return all raw data
    # TODO implements check duplicates url
    async for meta in extractor.async_walk_ongoing()[:3]:
        print(meta)


async def example_iter_objects():
    print("RUN ASYNC ITER OBJECTS")
    extractor = anilibria.Extractor()
    search = (await extractor.async_search("lain"))[0]
    ongoing = (await extractor.async_ongoing())[0]
    # return raw dict all metadata
    print("RUN SEARCH EXTRACT ALL METADATA")
    async for meta in search:
        print(meta)

    # return raw dict all metadata
    print("RUN ONGOING EXTRACT ALL METADATA")
    async for meta in ongoing:
        print(meta)

    anime = await search.a_get_anime()
    # iter search objects
    print("RUN ITER ANIME, EPISODE")
    async for episode in anime:
        async for video in episode:
            print(await video.a_get_source())

    # iter ongoing objects
    print("RUN ITER ANIME, EPISODE")
    anime_ongoing = await ongoing.a_get_anime()
    async for episode in anime_ongoing:
        async for video in episode:
            print(await video.a_get_source())


async def main():
    await step_by_step_search()
    await step_by_step_ongoing()
    await walk_search()
    await walk_ongoing()
    await example_iter_objects()


if __name__ == "__main__":
    asyncio.run(main())
