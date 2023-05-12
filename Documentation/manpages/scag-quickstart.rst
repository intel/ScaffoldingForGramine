.. program:: scag-quickstart
.. _scag-quickstart:

*********************************************************************
:program:`scag-quickstart` -- Build Gramine Scaffolding application
*********************************************************************

Synopsis
========

| :command:`scag quickstart`
| :command:`scag-quickstart`

Description
===========

This tool will guide interactivly user for each step of application
Scaffolding:

- setup,
- build,
- run.

The goal is to speed up the Scaffolding process for user, and get their application
up and running as fast as possible. Later on, users might want to do more advanced
configuration using :doc:`scag-setup`.
After changing the application, there is no need to run quickstart again; users
can simply rebuild the project using :doc:`scag-build`.

Usage for Human Interaction
===========================

:command:`scag-quickstart` is designed to be interactive and is intended for use by
humans who want a guided and hands-on experience while setting up their Gramine
caffolding application. It offers step-by-step instructions, making the scaffolding
process quick and easy.

Please note that the interface for :command:`scag-quickstart` may be unstable and
subject to variations between different versions of the tool.

For Automation and Advanced Configuration
=========================================

If developers wish to automate the scaffolding process or perform more advanced
configuration, it is recommended to use the :doc:`scag-setup`, and :doc:`scag-build`
tools. These tools provide programmatic interfaces and more extensive options for
customization.
