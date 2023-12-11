{% extends 'mmdebstrap-hooks/customize.sh' %}

{% block build %}
chroot "$1" sh -c "cd app && gradle build"
chroot "$1" rm -Rf /app/src
chroot "$1" gradle --stop
{% endblock %}

{#- vim: set ft=jinja : #}
