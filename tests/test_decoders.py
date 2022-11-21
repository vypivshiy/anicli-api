import pytest


from anicli_api.decoders import Aniboom, Kodik, BaseDecoder


def test_custom_decoder():
    class MyDecoder(BaseDecoder):
        @classmethod
        def parse(cls, url: str, **kwargs):
            return "test123"

        @classmethod
        async def async_parse(cls, url: str, **kwargs):
            ...

        @classmethod
        def _compare_url(cls, url: str):
            return "foobar" in url

    assert "foobar" == MyDecoder()
    assert "bazfoo" != MyDecoder()
    assert MyDecoder.parse("aaaaa") == "test123"


@pytest.mark.asyncio
async def test_async_custom_decoder():
    class MyDecoder(BaseDecoder):

        @classmethod
        def parse(cls, url: str, **kwargs):
            ...

        @classmethod
        async def async_parse(cls, url: str, **kwargs):
            return "test123"

        @classmethod
        def _compare_url(cls, url: str) -> bool:
            return "foobar" in url

    assert "foobar" == MyDecoder()
    assert "bazfoo" != MyDecoder()
    assert (await MyDecoder.async_parse("aaaaa")) == "test123"
