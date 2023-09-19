{% extends 'mmdebstrap-hooks/customize.sh' %}

{#
{% block install %}
{{ super() }}

chroot "$1" dotnet nuget --version
{% endblock %}
#}

{% block build %}
chroot "$1" dotnet build -c {{ build_config }} /app/{{ project_file | shquote }}
{% endblock %}

{#- vim: set ft=jinja : #}
