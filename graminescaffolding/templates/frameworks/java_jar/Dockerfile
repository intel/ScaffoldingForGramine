{% extends 'Dockerfile' %}

{% block install %}
{{ super() }}
{{ apt_install(
    'openjdk-17-jre-headless',
) }}
{% endblock %}

{#- vim: set ft=jinja : #}
