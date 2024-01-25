{% extends 'mmdebstrap-hooks/setup.sh' %}

{% block setup %}
install -D -t "$1"/usr/share/keyrings/ {{ scag.keys_path | shquote }}/microsoft-prod.gpg
{% endblock %}

{#- vim: set ft=jinja : #}
