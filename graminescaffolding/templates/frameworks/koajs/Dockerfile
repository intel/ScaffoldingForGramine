{% extends 'Dockerfile' %}

{% block install %}
RUN apt-get update && \
    apt-get install --no-install-recommends -y nodejs npm nginx
{% endblock %}

{% block copy_app %}
COPY . /app
RUN mkdir /confs /logs
COPY .scag/nginx.conf /confs
{% endblock %}

{% block post_copy_install %}
RUN npm install
{% endblock %}

{#- vim: set ft=jinja : #}
