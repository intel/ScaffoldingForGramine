{% extends 'Dockerfile' %}

{% block install %}
{{ super() }}
{{ apt_install(
    'nodejs',
    'npm',
    'nginx',
) }}
RUN npm install
{% endblock %}

{% block manifest_args -%}
    -Dapplication={{ application | shquote }}
{%- endblock %}

{#- vim: set ft=jinja : #}
