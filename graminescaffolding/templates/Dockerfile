{% set gramine = gramine if gramine is defined else 'gramine-sgx' -%}

ARG FROM
FROM ${FROM}

{% block workdir -%}
WORKDIR /app
{% endblock workdir -%}

{% block copy -%}
COPY . .
RUN ([ ! -d .scag/etc ] || cp -rT {{ scag.MAGIC_DIR | shquote }}/etc /usr/local/etc) && \
    cp -r {{ scag.MAGIC_DIR | shquote }}/app.manifest.template /app && \
    rm -Rf .scag
{% endblock copy -%}

{% block preinstall -%}
{% endblock preinstall -%}

{% block install -%}
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        {{ scag.builder.depends | map('shquote') | join(' ') }} && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
{% endblock install -%}

{% block build -%}
{% endblock build -%}

{% block manifest -%}
RUN gramine-manifest \
    -Dpassthrough_env={{ passthrough_env | join (':') }} \
    {% block manifest_args %}{% endblock %} \
    /app/app.manifest.template \
    /app/app.manifest
{%- endblock %}

{% block colophon -%}
{% block entrypoint -%}
ENTRYPOINT ["/bin/bash"]
{% endblock entrypoint -%}
{% block cmd -%}
CMD [{{ gramine | tojson}}, "app"]
{% endblock cmd -%}
{% endblock colophon %}

{#- vim: set ft=jinja : #}
