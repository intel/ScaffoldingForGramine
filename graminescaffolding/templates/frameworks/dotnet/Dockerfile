{% extends 'Dockerfile' %}

{% block install %}
RUN curl https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -o packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN rm packages-microsoft-prod.deb
RUN apt-get update && apt-get install -y dotnet-sdk-7.0
RUN dotnet nuget --version
{% endblock %}

{#- vim: set ft=jinja : #}
