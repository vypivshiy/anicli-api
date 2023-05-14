from anicli_api.source.animejoy import Extractor  # can usage any source


if __name__ == '__main__':
    ex = Extractor()
    print("PRESS CTRL + C for exit app")
    while True:
        results = ex.search(input("search query > "))
        print(*[f"{i}) {r}" for i, r in enumerate(results)], sep="\n")
        anime = results[int(input("anime > "))].get_anime()
        episodes = anime.get_episodes()
        print(*[f"{i}) {ep}" for i, ep in enumerate(episodes)], sep="\n")
        episode = episodes[int(input("episode > "))]
        sources = episode.get_sources()
        print(*[f"{i}) {source}" for i, source in enumerate(sources)], sep="\n")
        source = sources[int(input("source > "))]
        videos = source.get_videos()
        print(*[f"{i} {video}" for i, video in enumerate(videos)], sep="\n")
        video = videos[int(input("video > "))]
        print(video.type, video.quality, video.url, video.headers)
