#!/bin/sh

set -e

{% block install_keys %}
install -D \
    {{ scag.keys_path | shquote }}/gramine-2021.gpg \
    {{ scag.keys_path | shquote }}/intel-sgx-deb.asc \
    "$1"/etc/apt/trusted.gpg.d/
{% endblock %}

{#- vim: set ft=jinja : #}
