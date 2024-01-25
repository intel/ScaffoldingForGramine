{% extends 'Dockerfile' %}

{% block build %}
RUN gradle build && \
    rm -Rf /app/src
{% endblock %}

{#- vim: set ft=jinja : #}
