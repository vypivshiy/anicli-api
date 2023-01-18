from httpx import Client, Response
{% from "macro.p" import snake_to_camel %}

__all__ = (
    "Shikimori",
)

class ShikimoriApi:
    def __init__(self):
        self.session = Client()
        # all methods
        {% for cls_method in cls_methods -%}
        self.{{ cls_method }} = {{ snake_to_camel(cls_method) }}(self.session)
        {% endfor %}
{% include "sync_method.p" %}