{% extends 'Dockerfile' %}

{% block preinstall -%}
RUN apt-get update && \
    apt-get install --no-install-recommends -y ca-certificates && \
    echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" >> /etc/apt/sources.list.d/0000sources.list
{% endblock preinstall -%}

{% block build %}
RUN dotnet build -c {{ build_config }} /app/{{ project_file | shquote }}
{% endblock %}

{#- vim: set ft=jinja : #}
