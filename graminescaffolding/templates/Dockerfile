{# get_dockerfile -#}
{% block from %}
FROM gramineproject/gramine:v1.5
{% endblock %}

{% block workdir %}
WORKDIR /app
{% endblock %}

{% block confs %}
{% endblock %}

{% block install %}
{% endblock %}

{% block copy_app %}
COPY . /app
{% endblock %}

{% block post_copy_install %}
{% endblock %}

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

{# dockerfile_generate_manifest -#}
{%- block generate_manifest %}
RUN gramine-manifest -Dapplication=/app/{{ application }} {{ manifest_template }} {{ manifest }}
{% if executor == 'gramine-sgx' %}
RUN --mount=type=secret,id=sign,target=/tmp/sign \
    gramine-sgx-sign -k /tmp/sign --manifest {{ manifest }} --output {{ manifest }}.sgx
{% endif %}
{% endblock %}

{# dockerfile_generate_entrypoint -#}
ENTRYPOINT {{ [executor, 'app'] | tojson }}

{#- vim: set ft=jinja : #}
