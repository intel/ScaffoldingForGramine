***********************
Scaffolding for Gramine
***********************

Quick start (build from source)
===============================

.. code-block:: sh

    sudo apt-get build-dep . -t bullseye-backports
    debuild
    sudo apt-get install ../gramine-scaffolding_*.deb
    scag-quickstart

Development (editable install into virtualenv)
==============================================

.. code-block:: sh

    sudo apt-get install python3-venv
    python3 -m venv --system-site-packages .venv
    source .venv/bin/activate
    pip install --editable .
    scag-quickstart

.. vim: ts=4 sts=4 sw=4 et
