{% from "macro.p" import snake_to_camel %}
{%- for method_name, method_params in methods.items() %}
class {{ snake_to_camel(method_name) }}:
    def __init__(self, session: Client):
        self.session = session
    {% for method in method_params.methods %}
    {%- if fstring_params(method.apis[0].api_url) %}
    def {{ method.name }}(self, {{ fstring_params(method.apis[0].api_url) }}, method: str = "{{ method.apis[0].http_method }}", **kwargs) -> Response:
    {%- else %}
    def {{ method.name }}(self, method: str = "{{ method.apis[0].http_method }}", **kwargs) -> Response:
    {% endif %}
        """{% if method.apis[0].short_description %}{{ method.apis[0].short_description }} {% endif %}
        {% if method.params %}
        Params:
            {% for param in method.params %}
            {{ param.name }} ({{ param.expected_type }}) - {{ param.validator }} {{ param.description }} required={{ param.required }}
            {%- endfor %}
        {% endif %}
        Deprecated - {{ method.apis[0].deprecated }}

        Documentation: https://shikimori.one{{ method.doc_url }}
        """
        {%- if fstring_params(method.apis[0].api_url) %}
        return self.session.request(method, f"https://shikimori.one{{ fstring_url(method.apis[0].api_url) }}", **kwargs)
        {%- else %}
        return self.session.request(method, "https://shikimori.one{{ method.apis[0].api_url }}", **kwargs)
        {%- endif %}
    {% endfor %}
{% endfor %}
