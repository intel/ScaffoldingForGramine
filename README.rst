***********************
Scaffolding for Gramine
***********************

Quick start (build from source)
===============================

Debian 12, Ubuntu 23.04
-----------------------

.. code-block:: sh

    # sudo apt-get update && sudo apt-get install devscripts # if you didn't already
    sudo apt-get build-dep .
    debuild
    sudo apt-get install ../gramine-scaffolding_*.deb
    # gramine-sgx-gen-private-key # if you didn't already
    scag-quickstart

Debian 11
---------

.. code-block:: sh

    # sudo apt-get update && sudo apt-get install devscripts # if you didn't already
    sudo apt-get build-dep . -t bullseye-backports
    debuild
    sudo apt-get install ../gramine-scaffolding_*.deb
    # gramine-sgx-gen-private-key # if you didn't already
    scag-quickstart

Install into venv (for other distros, esp. for Ubuntu older than 23.04)
-----------------------------------------------------------------------

Unlike previous instructions, which build and install Scaffolding for all users
in the system, this stanza installs the project into python's virtual
environment. Those work only for single user, and either:
- each time you restart your shell, you need to source the ``activate`` script
  again; or
- call the binaries by their full path (e.g., ``.venv/bin/scag-build``); or
- add venv's ``bin/`` directory to ``$PATH`` environment variable.

First, install gramine as described in
https://gramine.rtfd.io/en/stable/installation.html#install-gramine-packages .
If you haven't generated an SGX signing key, you may want to consider executing
the following command

.. code-block:: sh

    gramine-sgx-gen-private-key

Then:

.. code-block:: sh

    sudo apt-get install docker.io python3-pip
    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install .
    scag-quickstart

Development (editable install into virtualenv)
==============================================

.. code-block:: sh

    sudo apt-get install gramine docker.io python3-venv
    python3 -m venv --system-site-packages .venv
    source .venv/bin/activate
    pip install --editable .
    scag-quickstart

.. vim: ts=4 sts=4 sw=4 et
