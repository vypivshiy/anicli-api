"""
Shikimori Codegen api wrapper
"""
import json
import re

import httpx
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader("dev", "templates"))


def fstring_url(url):
    result = re.findall(r"/:([\w_]+)", url)
    for r in result:
        url = re.sub(r":[\w_]+", "{%s}" % r, url)
    return url


def fstring_params(url):
    if params := re.findall(r"/:([\w_]+)", url):
        return ", ".join(params)
    return False


def download_doc_v1():
    return httpx.get("https://shikimori.one/api/doc/1.0").json()


def download_doc_v2():
    return httpx.get("https://shikimori.one/api/doc/2.0").json()


if __name__ == "__main__":
    data = download_doc_v1()["docs"]["resources"]

    code = env.get_template("sync_base_api.j2").render(
        cls_methods=list(data.keys()),
        methods=data,
        fstring_url=fstring_url,
        fstring_params=fstring_params,
    )

    with open("shikimori_sync.py", "w") as f:
        f.write(code)

    code = env.get_template("async_base_api.j2").render(
        cls_methods=list(data.keys()),
        methods=data,
        fstring_url=fstring_url,
        fstring_params=fstring_params,
    )

    with open("shikimori_async.py", "w") as f:
        f.write(code)
