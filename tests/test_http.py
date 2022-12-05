import pytest
from httpx import Request, Response

from anicli_api import BaseHTTPAsync, BaseHTTPSync, HTTPAsync, HTTPSync
from anicli_api._http import check_ddos_protect_hook


def test_singleton_sync():
    client_1, client_2 = HTTPSync(), HTTPSync()
    assert client_1 == client_2


def test_singleton_async():
    client_1, client_2 = HTTPAsync(), HTTPAsync()
    assert client_1 == client_2


def test_unescape():
    assert (
        BaseHTTPSync.unescape("{&quot;id&quot;:&quot;Jo9ql8ZeqnW&quot;,&")
        == '{"id":"Jo9ql8ZeqnW",&'
    )
    assert (
        BaseHTTPAsync.unescape("{&quot;id&quot;:&quot;Jo9ql8ZeqnW&quot;,&")
        == '{"id":"Jo9ql8ZeqnW",&'
    )


@pytest.mark.parametrize(
    "response",
    [
        Response(
            200,
            headers={"Server": "cloudflare", "Connection": "close"},
            request=Request("GET", "https://example.com"),
        ),
        Response(403, request=Request("GET", "https://example.com")),
    ],
)
def test_ddos_hook_check(response):
    with pytest.raises(ConnectionError):
        check_ddos_protect_hook(response)
