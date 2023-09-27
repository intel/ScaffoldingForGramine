{% extends 'Dockerfile' %}

{% block install %}
RUN apt-get update && \
    apt-get install --no-install-recommends -y python3.8 uwsgi nginx uwsgi-plugin-python3 python3-flask
{% endblock %}

{% block copy_app %}
COPY . /app
RUN mkdir /confs /logs
COPY .scag/nginx.conf /confs
{% endblock %}

{#- vim: set ft=jinja : #}
