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
Each framework can define additional specific for it options.

Options
=======

.. option:: --bootstrap

    Initialize an empty directory with an example application from
    the given framework.

.. option:: --framework <framework>

    The framework used by the scaffolded application.
    Currently, we support two frameworks:

    - Plain Python
    - Flask
    - Node.js

.. option:: --project_dir <dir>

    The directory of the application to scaffold.

.. option:: --passthrough_env

    Pass specific environment variables from the Docker environment into
    the Gramine process. The user can use this option multiple times to add
    many environment variables.

Python Options
==============

.. option:: --application

    Python application main script.

Node.js Options
===============

.. option:: --application

    Python application main script.

Files
=====

Example of the generated file:

.. code-block:: toml

    [application]
    framework = "python_plain"
    sgx = true

    [gramine]
    passthrough_env = []

    [python_plain]
    application = "hello_world.py"
