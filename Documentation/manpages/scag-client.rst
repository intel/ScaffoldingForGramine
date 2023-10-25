.. program:: scag-client
.. _scag-client:

***************************************************************
:program:`scag-client` -- HTTP client with attestation verifier
***************************************************************

Synopsis
========

| :command:`scag client` [*OPTIONS*] URL
| :command:`scag-client` [*OPTIONS*] URL

Description
===========

:program:`scag-client` is a curl-like tool for querying REST (HTTP) APIs exposed
by enclaves. The endpoint is a standard HTTPS URL, as supported by the enclave.

Options
=======

.. option:: --config <file>, -f <file>

    Path to :ref:`scag-client.toml <scag-client-toml>` config file that will be read.

.. option:: --project_dir <path>, -C <path>

    Path to build directory. If given, :ref:`scag-client.toml
    <scag-client-toml>` file will be read from
    :file:`{<path>}/.scag/scag-client.toml`.

.. option:: --request <method>, -X <method>

    Use specific HTTP method, rather than default ``GET``.

.. option:: --verify <attestation>

    Use specific attestation scheme. Overrides ``scag-client.attestation`` knob
    in config file. The list of valid values for this option is documented
    below, in the description of ``scag-client.attestation``.

.. option:: --output <path>, -o <path>

    Write the response body to this file. If not given or ``-``, write to
    standard output.

.. option:: --mrenclave <hex>

    Expect different MRENCLAVE than specified in config file. Overrides
    ``*.mrenclave`` option from config file.

.. option:: --mrsigner <hex>

    Expect different MRSIGNER than specified in config file. Overrides
    ``*.mrsigner`` option from config file.

.. option:: --allow-debug-enclave-insecure

    INSECURE. Allow to attest debug enclaves. Sets
    ``*.allow-debug-enclave-insecure`` in config file to ``true``.

.. option:: --no-allow-debug-enclave-insecure

    Forbid to attest debug enclaves. Sets ``*.allow-debug-enclave-insecure`` in
    config file to ``false``, which is the default, but might be used to
    override :option:`--allow-debug-enclave-insecure`.

.. option:: --allow-outdated-tcb-insecure

    INSECURE. Allow to attest enclaves running on outdated TCB (on CPUs with
    outdated microcode). Sets ``*.allow-outdated-tcb-insecure`` in config file
    to ``true``.

.. option:: --no-allow-outdated-tcb-insecure

    Forbid to attest enclaves running on outdated TCB (on CPUs with outdated
    microcode). Sets ``*.allow-outdated-tcb-insecure`` in config file to
    ``false``, which is the default, but might be used to override
    :option:`--allow-outdated-tcb-insecure`.

Environment
===========

``XDG_CONFIG_HOME``
    to determine last-resort location of configuration file.

.. _scag-client-toml:

Configuration file: :file:`scag-client.toml`
============================================

This file is written by :ref:`scag-build` and read in :ref:`scag-client`. It
contains default values that configure the attestation environment, like
type of attestation (DCAP, EPID, or MAA), expected MRENCLAVE and other
options.

The file is searched in three locations, in following order:

1. under the path specified in option :option:`--config`, if given;
2. in :file:`{<project_dir>}/.scag/scag-client.toml`, if option
   :option:`--project_dir` is given;
3. in :file:`{$HOME}/.config/gramine/scag-client.toml`
   (``XDG_CONFIG_HOME`` environment variable is taken into account)

The file can contain those keys:

General configuration
---------------------

``scag-config.attestation`` (string)
    One of:

    - ``DCAP``
    - ``EPID``
    - ``MAA``.

DCAP configuration
------------------

``dcap.*`` (table)
    Configuration pertaining to DCAP attestation.

``dcap.mrenclave`` (string of hex digits)
    Expected MRENCLAVE. If not given, MRENCLAVE is not checked.,

``dcap.mrsigner`` (string of hex digits)
    Expected MRSIGNER. If not given, MRSIGNER is not checked.,

``dcap.isv-prod-id`` (number)
    Expected ISV_PROD_ID. If not given, ISV_PROD_ID is not checked.

``dcap.isv-svn`` (number)
    Expected ISV_SVN. If not given, ISV_SVN is not checked.

``dcap.allow-debug-enclave-insecure`` (bool, default false)
    INSECURE, DO NOT USE IN PRODUCTION! Allow debug enclaves to be attested.

``dcap.allow-outdated_tcb-insecure`` (bool, default false)
    INSECURE, DO NOT USE IN PRODUCTION! Allow enclaves executed on CPUs with
    outdated microcode.

``dcap.allow-hw-config-needed`` (bool, default false)
    Allow HW_CONFIG_NEEDED response.

``dcap.allow-sw-hardening-needed`` (bool, default false)
    Allow SW_HARDENING_NEEDED response.

EPID configuration
------------------

``epid.*`` (table)
    Configuration pertaining to EPID attestation.

``epid.epid-api-key`` (string)
    Key to IAS REST API. Mandatory.

``epid.mrenclave`` (string of hex digits)
    Expected MRENCLAVE. If not given, MRENCLAVE is not checked.,

``epid.mrsigner`` (string of hex digits)
    Expected MRSIGNER. If not given, MRSIGNER is not checked.,

``epid.isv-prod-id`` (number)
    Expected ISV_PROD_ID. If not given, ISV_PROD_ID is not checked.

``epid.isv-svn`` (number)
    Expected ISV_SVN. If not given, ISV_SVN is not checked.

``epid.allow-debug-enclave-insecure`` (bool, default false)
    INSECURE, DO NOT USE IN PRODUCTION! Allow debug enclaves to be attested.

``epid.allow-outdated-tcb-insecure`` (bool, default false)
    INSECURE, DO NOT USE IN PRODUCTION! Allow enclaves executed on CPUs with
    outdated microcode.

``epid.allow-hw-config-needed`` (bool, default false)
    Allow HW_CONFIG_NEEDED response.

``epid.allow-sw-hardening-needed`` (bool, default false)
    Allow SW_HARDENING_NEEDED response.

``epid.ias-report-url`` (string)
    URL to IAS REPORT API. See IAS API documentation for more info.

``epid.ias-sigrl-url`` (string)
    URL to IAS REPORT API. See IAS API documentation for more info.

``epid.ias-pub-key-pem``
    TODO

MAA configuration
-----------------

``maa.*`` (table)
    Configuration pertaining to MAA attestation.

``maa.maa-provider-url`` (string)
    URL to MAA REST API. Mandatory.

``maa.mrenclave`` (string of hex digits)
    Expected MRENCLAVE. If not given, MRENCLAVE is not checked.

``maa.mrsigner`` (string of hex digits)
    Expected MRSIGNER. If not given, MRSIGNER is not checked.

``maa.isv-prod-id`` (number)
    Expected ISV_PROD_ID. If not given, ISV_PROD_ID is not checked.

``maa.isv-svn`` (number)
    Expected ISV_SVN. If not given, ISV_SVN is not checked.

``maa.allow-debug-enclave-insecure`` (bool, default false)
    INSECURE, DO NOT USE IN PRODUCTION! Allow debug enclaves to be attested.

``maa.maa-provider-api-version`` (number)
    Version of the MAA API. See ``libra_tls_verify_maa`` documentation for more
    info.

Exit status
===========

On success, exits with 0. On failures, exits non-zero and prints diagnostics to
stderr.

Examples
========

.. code-block:: sh

    scag-quickstart --project_dir app --framework flask --bootstrap
    cd app
    scag-build
    docker run ... -p 8000:8000
    scag-client -C . https://localhost:8000
