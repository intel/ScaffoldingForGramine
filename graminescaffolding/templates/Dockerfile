{% set gramine = gramine if gramine is defined else 'gramine-sgx' -%}

FROM scratch
ADD .scag/rootfs.tar /
WORKDIR /app
ENTRYPOINT ["/bin/bash"]
CMD [{{ gramine | tojson}}, "app"]

{#- vim: set ft=jinja : #}
