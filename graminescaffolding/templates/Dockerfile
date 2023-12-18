{% set gramine = gramine if gramine is defined else 'gramine-sgx' -%}

FROM scratch

{% block add -%}
ADD .scag/rootfs.tar /
{% endblock add -%}

{% block local -%}
{% endblock local -%}

{% block colophon -%}
{% block workdir -%}
WORKDIR /app
{% endblock workdir -%}
{% block entrypoint -%}
ENTRYPOINT ["/bin/bash"]
{% endblock entrypoint -%}
{% block cmd -%}
CMD [{{ gramine | tojson}}, "app"]
{% endblock cmd -%}
{% endblock colophon %}

{#- vim: set ft=jinja : #}
