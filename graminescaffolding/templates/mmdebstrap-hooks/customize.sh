#!/bin/sh

set -e

{% block install -%}
cp -r {{ scag.builder.project_dir }} "$1"/app
{%- endblock %}

{% block manifest -%}
chroot "$1" gramine-manifest \
    {% block manifest_args %}{% endblock %} \
    /app/.scag/app.manifest.template \
    /app/app.manifest
{%- endblock %}

{% block sign -%}
gramine-sgx-sign \
    --date 0000-00-00 \
    {% block sign_args %}{{ sgx.sign_args | default([]) | map('shquote') | join(' ') }}{% endblock %} \
    --chroot "$1" \
    --manifest "$1"/app/app.manifest \
    --output "$1"/app/app.manifest.sgx
{%- endblock %}

{#- vim: set ft=jinja : #}
