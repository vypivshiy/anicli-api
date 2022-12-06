from anicli_api.extractors import anilibria


def step_by_step_search():
    """simple usage api search example"""
    # init extractor
    print("RUN STEP BY STEP SEARCH")
    extractor = anilibria.Extractor()
    # search by string query
    search = extractor.search("lain")
    print(search[0].dict())  # dict method return all keys
    # step-by-step get objects
    anime = search[0].get_anime()
    episodes = anime.get_episodes()
    videos = episodes[0].get_videos()
    links = videos[0].get_source()
    # get first direct links dict
    print(links)


def step_by_step_ongoing():
    """simple usage api ongoing example"""
    print("RUN STEP BY STEP ONGOING")
    extractor = anilibria.Extractor()
    # get all available ongoings
    ongoings = extractor.ongoing()
    ongoing = ongoings[0]
    print(ongoing.dict())
    anime = ongoing.get_anime()
    episodes = anime.get_episodes()
    videos = episodes[0].get_videos()
    links = videos[0].get_source()
    print(links)


def walk_search():
    """simple usage api walk_search example"""
    extractor = anilibria.Extractor()
    # method return all raw data
    print("RUN WALK SEARCH")
    for meta in extractor.walk_search("school"):
        print(meta)


def walk_ongoing():
    """simple usage api walk_ongoing example"""
    print("RUN WALK ONGOING")
    extractor = anilibria.Extractor()
    # method return all raw data
    # TODO implements check duplicates url
    for meta in extractor.walk_ongoing()[:3]:
        print(meta)


def example_iter_objects():
    print("RUN ITER OBJECTS EXAMPLE")
    extractor = anilibria.Extractor()
    search = extractor.search("lain")[0]
    ongoing = extractor.ongoing()[0]
    # return raw dict all metadata
    print("SEARCH extract all meta")

    for meta in search:
        print(meta)

    # return raw dict all metadata
    print("ONGOING extract all meta")
    for meta in ongoing:
        print(meta)

    anime = search.get_anime()
    # iter search objects
    print("ANIME, EPISODE iter")
    for episode in anime:
        for video in episode:
            print(video.get_source())

    # iter ongoing objects
    anime_ongoing = ongoing.get_anime()
    for episode in anime_ongoing:
        for video in episode:
            print(video.get_source())


if __name__ == "__main__":
    step_by_step_search()
    step_by_step_ongoing()
    walk_search()
    walk_ongoing()
    example_iter_objects()
