.. program:: scag-setup
.. _scag-setup:

*********************************************************************
:program:`scag-setup` -- Build Gramine Scaffolding application
*********************************************************************

Synopsis
========

| :command:`scag setup` [*OPTIONS*]
| :command:`scag-setup` [*OPTIONS*]

Description
===========

This command is used to configure the Scaffolding project.
As an output, the configuration file is generated.
The file contains all necessary information required to build the project.

Options
=======

.. option:: --framework <framework>

    The framework used by the scaffolded application.
    Currently, we support two frameworks:

    - Plain Python
    - Flask


.. option:: --sgx

    Scaffold application using Intel Software Guard Extensions (Intel SGX).

.. option:: --sgx_key <file>

    Path to the private key used for signing. This will save a
    path to the private key in the configuration file.
    This can be useful if the application uses a dedicated private
    key, instead of the user one.

.. option:: --project_dir <dir>

    The directory of the application to scaffold.

Files
=====

Example of the generated file:

.. code-block:: toml

    [application]
    framework = "python_plain"
    sgx = true

    [python_plain]
    application = "hello_world.py"
