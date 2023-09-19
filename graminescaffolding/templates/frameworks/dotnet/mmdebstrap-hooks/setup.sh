{% extends 'mmdebstrap-hooks/setup.sh' %}

{% block install_keys %}
{{ super() }}

install -D -t "$1"/etc/apt/trusted.gpg.d/ {{ scag.keys_path | shquote }}/microsoft-prod.gpg
{% endblock %}

{#- vim: set ft=jinja : #}
