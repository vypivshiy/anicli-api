"""optional module for extract cookies from browsers.

Implemented for helps avoid anidddos, antifrod, auth protects.
Simular as yt-dlp --cookies and --cookies-from-browser options.

USAGE EXAMPLE:

>>> from anicli_api.tools.cookies import get_raw_cookies_from_browser, raw_cookies_to_httpx_cookiejar
>>> # as default, get any browser
>>> # optional, can be filtered by domain(s)
>>> raw_cookies = get_raw_cookies_from_browser(domains=["github.com", "example.com"])
>>> cookies = raw_cookies_to_httpx_cookiejar(raw_cookies)
>>> import httpx
>>> httpx.get("https://github.com", cookies=cookies)
>>> # convert to netscape format
>>> from anicli_api.tools.cookies import raw_cookies_to_netscape
>>> raw_cookies_to_netscape(raw_cookies)

"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import rookiepy
except ImportError:
    # we don't throw an error because it is still possible to load from netscape format string/file
    rookiepy = None
from typing import Literal, Optional, Any, Union
from httpx import Cookies


if sys.platform == "darwin":
    BROWSER_LITERAL = Literal[
        "firefox",
        "librewolf",
        "brave",
        "edge",
        "chrome",
        "chromium",
        "arc",
        "opera",
        "opera_gx",
        "vivaldi",
        "chromium_based",
        "firefox_based",
        "any_browser",
        "safari",
    ]
elif sys.platform == "win32":
    BROWSER_LITERAL = Literal[
        "firefox",
        "librewolf",
        "brave",
        "edge",
        "chrome",
        "chromium",
        "arc",
        "opera",
        "opera_gx",
        "vivaldi",
        "chromium_based",
        "firefox_based",
        "any_browser",
        # lib support it, why not?
        "internet_explorer",
        "octo_browser",
    ]
else:
    BROWSER_LITERAL = Literal[
        "firefox",
        "librewolf",
        "brave",
        "edge",
        "chrome",
        "chromium",
        "arc",
        "opera",
        "opera_gx",
        "vivaldi",
        "chromium_based",
        "firefox_based",
        "any_browser",
    ]


def __is_installed_rookiepy() -> None:
    if not rookiepy:
        msg = (
            "Extract cookies from browser required 'rookiepy' dependency. "
            "For install it use `pip install anicli-api[browser-cookies]` command."
        )
        raise ImportError(msg)


def get_raw_cookies_from_browser(
    browser: BROWSER_LITERAL = "any_browser", domains: Optional[list[str]] = None
) -> list[dict[str, Any]]:
    """extract cookies from browser. Optional, can be filtered by list of domains."""
    if not rookiepy:
        msg = (
            "Extract cookies from browser required 'rookiepy' dependency. "
            "For install it use `pip install anicli-api[browser-cookies]` command."
        )
        raise ImportError(msg)
    try:
        func_extract = getattr(rookiepy, browser)
    except AttributeError:
        msg = f"rookiepy not implemented browser '{browser}'"
        raise AttributeError(msg)
    return func_extract(domains)


def raw_cookies_to_httpx_cookiejar(raw_cookies: list[dict[str, Any]]) -> Cookies:
    """convert raw cookies to httpx.Cookies format"""
    __is_installed_rookiepy()
    cookie_jar = rookiepy.to_cookiejar(raw_cookies)
    return Cookies(cookie_jar)


def raw_cookies_to_netscape(raw_cookies: list[dict[str, Any]]) -> str:
    """convert list of cookies to netscape format"""
    __is_installed_rookiepy()
    return rookiepy.to_netscape(raw_cookies)


def parse_netscape_cookie_line(netscape_cookie_line: str) -> dict[str, Any]:
    line = netscape_cookie_line.strip()

    # Skip empty lines and comments
    if not netscape_cookie_line or line.startswith("#"):
        return {}

    parts = line.split("\t")

    # Skip lines with incorrect number of fields
    if len(parts) != 7:
        return {}

    domain, domain_flag, path, secure, expires, name, value = parts

    return {
        "domain": domain,
        "flag": domain_flag == "TRUE",  # Convert to boolean
        "path": path,
        "secure": secure == "TRUE",  # Convert to boolean
        "expires": int(expires),  # Convert to timestamp
        "name": name,
        "value": value,
    }


def parse_netscape_cookie_string(netscape_cookie_string: str) -> list[dict[str, Any]]:
    cookies = []
    for line in netscape_cookie_string.splitlines():
        cookie = parse_netscape_cookie_line(line)
        if not cookie:
            continue
        cookies.append(cookie)
    return cookies


def parse_netscape_cookies_file(cookie_file: Union[str, Path]) -> list[dict[str, Any]]:
    """
    Parse Netscape format cookies file into a list of dictionaries.

    Args:
        cookie_file: Path to the cookies file in Netscape format

    Returns:
        List of cookie dictionaries with keys:
        domain, flag, path, secure, expires, name, value
    """
    cookies = []
    with open(cookie_file, "r", encoding="utf-8") as f:
        for line in f:
            cookie = parse_netscape_cookie_line(line)
            if not cookie:
                continue
            cookies.append(cookie)
    return cookies
