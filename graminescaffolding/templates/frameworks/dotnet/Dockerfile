{% extends 'Dockerfile' %}

{% block install -%}
{{ apt_install('ca-certificates') }}

RUN echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" >> /etc/apt/sources.list.d/0000sources.list

{{ super() }}

{{ apt_install('dotnet-sdk-7.0') }}
{% endblock -%}

{% block build %}
RUN dotnet build -c {{ build_config }} /app/{{ project_file | shquote }}
{% endblock %}

{#- vim: set ft=jinja : #}
