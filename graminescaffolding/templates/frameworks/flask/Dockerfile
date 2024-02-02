{% extends 'Dockerfile' %}

{% block install %}
{{ super() }}
{{ apt_install(
    'nginx',
    'python3-flask',
    'python3.11',
    'uwsgi',
    'uwsgi-plugin-python3',
) }}
{% endblock %}

{#- vim: set ft=jinja : #}
