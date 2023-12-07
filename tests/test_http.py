from typing import List

import pytest
from httpx import ConnectError

from anicli_api.base import BaseExtractor, HTTPAsync, HTTPRetryConnectSyncTransport, HTTPSync
from anicli_api.player.base import BaseVideoExtractor, Video


class MockVideoExtractor(BaseVideoExtractor):
    DEFAULT_HTTP_CONFIG = {"headers": {"user-agent": "mock-user-agent"}}

    def parse(self, url: str, **kwargs) -> List[Video]:
        return []

    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        return []


class MockRetryTransport(HTTPRetryConnectSyncTransport):
    ATTEMPTS_CONNECT = 1
    DELAY_INCREASE_STEP = 0
    RETRY_CONNECT_DELAY = 0.000001


def test_http_client_patch():
    # default config
    client = BaseExtractor.HTTP()
    # HTTPRetryConnectSyncTransport
    old_transport = client._transport.__class__.__name__

    # config transport
    client_2 = HTTPSync(transport=None)
    new_transport = client._transport.__class__.__name__
    assert client == client_2
    assert old_transport != new_transport


def test_retry_transport(caplog):
    client = HTTPSync(transport=MockRetryTransport())
    with pytest.raises(ConnectError):
        client.get("https://example.comwtfmeme")

    assert all(
        record.message == "[1] ConnectError, GET https://example.comwtfmeme try retry connect"
        for record in caplog.records
    )


def test_async_http_client_patch():
    # default config
    client = BaseExtractor.HTTP_ASYNC()
    # HTTPRetryConnectSyncTransport
    old_transport = client._transport.__class__.__name__

    # config transport
    client_2 = HTTPAsync(transport=None)
    new_transport = client._transport.__class__.__name__
    assert client == client_2
    assert old_transport != new_transport


def test_player_extractor_http_path():
    ex = MockVideoExtractor()
    ex2 = MockVideoExtractor(transport=None, headers={"User-Agent": "test-agent"})
    assert ex.http.headers["user-agent"] == "mock-user-agent"
    assert ex.a_http.headers["user-agent"] == "mock-user-agent"
    assert ex2.http.headers["user-agent"] == "test-agent"
    assert ex2.a_http.headers["user-agent"] == "test-agent"
