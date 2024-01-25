{% extends 'Dockerfile' %}

{% block install %}
{{ super() }}
RUN npm install
{% endblock %}

{% block manifest_args -%}
    -Dapplication={{ application | shquote }}
{%- endblock %}

{#- vim: set ft=jinja : #}
