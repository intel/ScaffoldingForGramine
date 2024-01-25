{% set gramine = gramine if gramine is defined else 'gramine-sgx' -%}

FROM scratch

{% block add -%}
ADD .scag/rootfs.tar /
{% endblock add -%}

{% block workdir -%}
WORKDIR /app
{% endblock workdir -%}

{% block preinstall -%}
{% endblock preinstall -%}

{% block install -%}
RUN apt-get update && \
    apt-get install --no-install-recommends -y {{ scag.builder.depends | join(' ') }} && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
{% endblock install -%}

{% block copy -%}
COPY . /app
RUN mv {{ scag.MAGIC_DIR }}/app.manifest.template /app && \
    mv {{ scag.MAGIC_DIR | shquote }}/etc /usr/local/
{% endblock copy -%}

{% block local -%}
{% endblock local -%}

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
