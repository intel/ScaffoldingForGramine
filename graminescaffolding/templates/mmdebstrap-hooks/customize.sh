#!/bin/sh

set -e

{% block install -%}
cp -rT {{ scag.builder.project_dir | shquote }} "$1"/app
rm -rf "$1"/app/.scag
cp -r {{ scag.builder.magic_dir | shquote }}/app.manifest.template "$1"/app

if test -d {{ scag.builder.magic_dir | shquote }}/etc
then
    cp -rT  "$1"/usr/local/etc
fi
{%- endblock %}

{% block manifest -%}
chroot "$1" gramine-manifest \
    {% block manifest_args %}{% endblock %} \
    /app/app.manifest.template \
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
