#!/bin/sh

set -e

{% block defualtkeys %}
install -D -t "$1"/etc/apt/trusted.gpg.d/ {{ scag.keys_path | shquote }}/trusted.gpg.d/*
{% endblock %}

{% block setup %}
{% endblock %}

{#- vim: set ft=jinja : #}
