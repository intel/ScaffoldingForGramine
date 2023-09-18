{% extends 'mmdebstrap-hooks/customize.sh' %}

{% block install %}
{{ super() }}
chroot "$1" sh -c 'cd /app; npm install'
{% endblock %}

{% block manifest_args -%}
    -Dapplication={{ application | shquote }}
{%- endblock %}

{#- vim: set ft=jinja : #}
