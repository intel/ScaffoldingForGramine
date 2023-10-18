{% extends 'mmdebstrap-hooks/customize.sh' %}

{% block manifest_args %}-Dapplication={{ application | shquote }}{% endblock %}

{#- vim: set ft=jinja : #}
