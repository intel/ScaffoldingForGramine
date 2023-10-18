.. highlight:: toml

Configuration
=============

SCAG is configured in file:`scag.toml`, which should be placed in main directory
of the app and committed to the repository.

See https://toml.io/ for the description of the TOML format.

The following configuration knobs are available:

General options
---------------

``application.framework`` (string)
    Framework. One of ``python_plain``, ``flask``, ``nodejs_plain``.

``sgx.sign_args`` (array)
    Extra arguments to :command:`gramine-sgx-sign` command. Can be used to
    specify alternative RSA key, or use plugins.

    .. code-block::

        [sgx]
        sign_args = ['--key', 'example.pem']

Options specific to ``flask`` framework
----------------------------------------------

(none)

Options specific to ``nodejs_plain`` framework
----------------------------------------------

``nodejs_plain.application`` (string)
    Path to the main script inside application's directory.

Options specific to ``python_plain`` framework
----------------------------------------------

``python_plain.application`` (string)
    Path to the main script inside application's directory.
