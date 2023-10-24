***********************
Scaffolding for Gramine
***********************

Quick start (build from source)
===============================

Steps common to all distros
---------------------------

In this 0.1 release, you need Gramine 1.6, which is yet unreleased at the time
of this writing, so until Gramine 1.6 is released, you need to install Gramine
1.6 from unstable repositories. To do this, please prefix distro codename with
``unstable-`` when following installation instructions for Gramine. Codename is
e.g., ``bookworm`` for Debian 12, but for Ubuntu this might be written as
``$(lsb_release -sc)`` substitution in the manual.

For example, when installing on Debian 12, add repositories like this:

.. code-block:: sh

    sudo curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ unstable-bookworm main" \
    | sudo tee /etc/apt/sources.list.d/gramine.list

    sudo curl -fsSLo /usr/share/keyrings/intel-sgx-deb.asc https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-sgx-deb.asc] https://download.01.org/intel-sgx/sgx_repo/ubuntu jammy main" \
    | sudo tee /etc/apt/sources.list.d/intel-sgx.list

Then you install Gramine as usual:

.. code-block:: sh

    apt-get update
    apt-get install gramine

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
