{# get_dockerfile -#}
{% block from %}
FROM gramineproject/gramine:v1.5
{% endblock %}

{% block workdir %}
WORKDIR /app
{% endblock %}

{% block confs %}
{% endblock %}

RUN apt-get update
{% block install %}
{% endblock %}

{% block copy_app %}
COPY . /app
{% endblock %}

{# dockerfile_generate_manifest -#}
{% block generate_manifest %}
RUN gramine-manifest -Dapplication=/app/{{ application }} {{ manifest_template }} {{ manifest }}
{% if executor == 'gramine-sgx' %}
RUN --mount=type=secret,id=sign,target=/tmp/sign \
    gramine-sgx-sign -k /tmp/sign --manifest {{ manifest }} --output {{ manifest }}.sgx
{% endif %}
{% endblock %}

{# dockerfile_generate_entrypoint -#}
ENTRYPOINT {{ [executor, 'app'] | tojson }}

{#- vim: set ft=jinja : #}
