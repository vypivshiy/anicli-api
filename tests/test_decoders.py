import re

import pytest

from anicli_api.base_decoder import BaseDecoder


@pytest.mark.asyncio
async def test_custom_decoder():
    class MyDecoder(BaseDecoder):
        URL_RULE = re.compile(r"foobar")

        @classmethod
        def parse(cls, url: str, **kwargs):
            cls._validate_url(url)
            return "test123"

        @classmethod
        async def async_parse(cls, url: str, **kwargs):
            cls._validate_url(url)
            return "test123"

    assert "foobar" == MyDecoder()
    assert "bazfoo" != MyDecoder()
    with pytest.raises(TypeError):
        await MyDecoder.async_parse("aaaaa")

    with pytest.raises(TypeError):
        MyDecoder.parse("aaaa")

    assert MyDecoder.parse("foobar/aaaa") == "test123"
    assert (await MyDecoder.async_parse("foobar/aaaaa")) == "test123"
