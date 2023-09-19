{% extends 'mmdebstrap-hooks/setup.sh' %}

{% block install_keys %}
{{ super() }}

install -D -t "$1"/usr/share/keyrings/microsoft-prod.gpg {{ scag.keys_path | shquote }}/microsoft-prod.gpg
{% endblock %}

{#- vim: set ft=jinja : #}
