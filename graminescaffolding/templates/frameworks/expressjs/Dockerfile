{% extends 'Dockerfile' %}

{% block local %}
RUN npm install
{% endblock %}

{% block manifest_args -%}
    -Dapplication={{ application | shquote }}
{%- endblock %}

{#- vim: set ft=jinja : #}
