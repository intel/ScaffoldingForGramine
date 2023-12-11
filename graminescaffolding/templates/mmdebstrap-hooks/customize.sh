#!/bin/sh

set -e

{% block install -%}
cp -rT {{ scag.builder.project_dir | shquote }} "$1"/app
rm -rf "$1"/app/.scag
cp -r {{ scag.builder.magic_dir | shquote }}/app.manifest.template "$1"/app

if test -d {{ scag.builder.magic_dir | shquote }}/etc
then
    cp -rT {{ scag.builder.magic_dir | shquote }}/etc "$1"/usr/local/etc
fi
{%- endblock %}

{% block build -%}
{%- endblock %}

{% block manifest -%}
chroot "$1" gramine-manifest \
    -Dpassthrough_env={{ passthrough_env | join (':') }} \
    {% block manifest_args %}{% endblock %} \
    /app/app.manifest.template \
    /app/app.manifest
{%- endblock %}

{#- vim: set ft=jinja : #}
