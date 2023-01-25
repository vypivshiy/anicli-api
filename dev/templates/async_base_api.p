from httpx import AsyncClient, Response
{% from "macro.p" import snake_to_camel %}
__all__ = (
    "ShikimoriApiAsync",
)


class ShikimoriApiAsync:
    def __init__(self):
        self.session = AsyncClient()
        # all methods
        {% for cls_method in cls_methods -%}
        self.{{ cls_method }} = Async{{ snake_to_camel(cls_method) }}(self.session)
        {% endfor %}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
{% include "async_method.p" %}