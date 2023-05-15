from urllib.parse import urlsplit

from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader("dev", "templates"))


if __name__ == "__main__":
    base_url = input("past base url entrypoint > ")
    if not base_url.startswith("https://"):
        base_url = f"https://{base_url}"
    if base_url.endswith("/"):
        base_url = base_url.rstrip("/")

    netloc = urlsplit(base_url).netloc.split(".")[0]
    code = env.get_template("anicli_api_source.j2").render(
        base_url=base_url, source_name=netloc.title()
    )
    print(f"generated snippet: {netloc}.py")
    with open(f"{netloc}.py", "w") as f:
        f.write(code)
