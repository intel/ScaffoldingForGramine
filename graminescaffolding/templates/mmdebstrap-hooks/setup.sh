#!/bin/sh

set -e

install -D -t "$1"/etc/apt/trusted.gpg.d/ {{ scag.keys_path | shquote }}/*

{#- vim: set ft=jinja : #}
