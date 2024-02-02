{% extends 'Dockerfile' %}

{% block install %}
{{ super() }}
{{ apt.install(
    'openjdk-17-jre-headless',
) }}
{% endblock %}

{#- vim: set ft=jinja : #}
