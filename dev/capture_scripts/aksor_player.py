import httpx
import re

IFRAME_URL_RE = re.compile(r"aksor\.tv/video/([a-f0-9]+)")
API_URL = "https://player.aksor.tv/api/video/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
    "Accept": "application/json",
    "Referer": "https://old.yummyani.me/",
}


def extract_stream_url(iframe_url: str) -> str:
    m = IFRAME_URL_RE.search(iframe_url)
    if not m:
        raise ValueError(f"Cannot extract video id from: {iframe_url}")
    video_id = m.group(1)

    resp = httpx.get(API_URL.format(video_id), headers=HEADERS, follow_redirects=True)
    resp.raise_for_status()
    data = resp.json()

    qualities = data["qualities"]
    for key in ("q4k", "q2k", "q1080", "q720", "q480", "q360"):
        url = qualities.get(key)
        if url:
            return url

    raise ValueError(f"No quality streams found for {video_id}")


if __name__ == "__main__":
    url = extract_stream_url("https://player.aksor.tv/video/6e497a9db21b99162350c5153bd25a48")
    print(url)
