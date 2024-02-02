{% extends 'Dockerfile' %}

{% block install %}
{{ super() }}
{{ apt.install(
    'python3.11',
) }}
{% endblock %}

{% block manifest_args -%}
    -Dapplication={{ application | shquote }}
{%- endblock %}

{#- vim: set ft=jinja : #}
