{% macro snake_to_camel(snake_string) %}
    {%- set camel_string = snake_string.replace('_', ' ') -%}
    {%- set camel_string = camel_string.title().replace(' ', '') -%}
    {{- camel_string[0].upper() }}{{ camel_string[1:] -}}
{% endmacro %}
