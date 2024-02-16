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


def test_retry_transport(caplog):
    client = HTTPSync(transport=MockRetryTransport())
    with pytest.raises(ConnectError):
        client.get("https://example.comwtfmeme")

    assert caplog.records[0].message.startswith("[1] ConnectError: [Errno -2]")


def test_player_extractor_http_path():
    ex = MockVideoExtractor()
    ex2 = MockVideoExtractor(transport=None, headers={"User-Agent": "test-agent"})
    assert ex.http.headers["user-agent"] == "mock-user-agent"
    assert ex.a_http.headers["user-agent"] == "mock-user-agent"
    assert ex2.http.headers["user-agent"] == "test-agent"
    assert ex2.a_http.headers["user-agent"] == "test-agent"
