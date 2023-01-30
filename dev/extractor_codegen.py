import argparse
import pathlib
from urllib.parse import parse_qs, urlsplit

from jinja2 import Environment, PackageLoader

ENV = Environment(loader=PackageLoader("dev", "templates"))

if __name__ == "__main__":
    EXTRACTORS_PATH = pathlib.Path("..")
    DECODERS_PATH = pathlib.Path("..")
else:
    EXTRACTORS_PATH = pathlib.Path(".")
    DECODERS_PATH = pathlib.Path(".")


def argument_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["create"])
    parser.add_argument("choice", choices=["extractor", "decoder"])
    return parser.parse_args()


def main():
    namespace = argument_parser()
    command = namespace.command
    choice = namespace.choice
    if command == "create":
        if choice == "extractor":
            # https://animania.online/index.php
            base_url = input("Write base_url (with http(s)://) > ")
            # https://animania.online/index.php?do=search&subaction=search&story=lain
            search_url = input("Write search_url url entrypoint (skip if not GET request) > ")
            if not search_url:
                search_url = base_url
                _params = "{}"
            else:
                _url = urlsplit(search_url)
                _params = str({k: v[0] for k, v in parse_qs(_url.query).items()})
                print(_params)
                search_url = f"{_url.scheme}://{_url.netloc}{_url.path}"
            ongoing_url = input("Write ongoing_url page entrypoint (default: base_url) > ")
            if not ongoing_url:
                ongoing_url = base_url

            template = ENV.get_template("extractor.p").render(
                base_url=base_url, search_url=search_url, ongoing_url=ongoing_url, params=_params
            )
            with open(f"{urlsplit(base_url).netloc.replace('.', '_')}.py", "w") as f:
                f.write(template)

        elif choice == "decoder":
            url = input("enter decoder url (with http(s)://) > ")
            url = urlsplit(url)
            url_re = url.netloc.replace(".", r"\.")
            url_rule = input(f"Enter regex rule validator (default: https?://{url_re} >")
            if not url_rule:
                url_rule = url_re

            decoder_name = url.netloc.split(".")[0].title()
            template = ENV.get_template("decoder.p").render(
                decoder_name=decoder_name, url_rule=url_rule
            )
            with open(f"{decoder_name.lower()}.py", "w") as f:
                f.write(template)


if __name__ == "__main__":
    main()
