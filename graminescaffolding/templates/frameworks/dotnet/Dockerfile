{% extends 'Dockerfile' %}

{% block preinstall %};
COPY {{ scag.keys_path | shquote }}/microsoft-prod.gpg /usr/share/keyrings/microsoft-prod.gpg
{% endblock %}

{% block build %}
RUN dotnet build -c {{ build_config }} /app/{{ project_file | shquote }}
{% endblock %}

{#- vim: set ft=jinja : #}
