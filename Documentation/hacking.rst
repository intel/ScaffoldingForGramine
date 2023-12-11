Developer HOWTO
===============

This document is intended for people who want to add support for new framework.

How it works
------------

There's a class called ``Builder`` (see :file:`gramineproject/builder.py`) which
directs the whole process of building the container. The build is composed of
steps:

1. Templates are rendered into magic directory.
2. System image is installed into chroot directory.
3. Image is customised and signed.

Templates are found in :file:`gramineproject/templates/framework/{<framework>}`
directory or directly in :file:`gramineproject/templates`. They are rendered
into files in subdirectory :file:`.scag` placed next to :file:`scag.toml` in
root directory of the project. There are a few common templates that are
rendered for every build (like ``app.manifest.template`` and ``Dockerfile``),
and frameworks may render additional templates as required.

Steps 2-3 are executed as single command, ``mmdebstrap``. ``mmdebstrap`` is
a tool for creating Debian-based system images. The process is customisable with
*hooks*. There are two hooks used by scaffolding:

- ``setup`` (rendered as :file:`.scag/mmdebstrap-hooks/setup.sh`): Runs very
  early in the bootstrap process and prepares installation environment. Probably
  should not be touched unless you need to pin some packages for reproducible
  builds.

- ``customize`` (rendered as :file:`.scag/mmdebstrap-hooks/setup.sh`): Runs
  after all deb packages have been installed. This is step 3: it copies the app
  to :file:`/app` inside the chroot, then renders the manifest inside the chroot
  using ``gramine-manifest`` and signs the enclave with ``gramine-sgx-sign``.

  If you want to adjust ``gramine-manifest`` or ``gramine-sgx-sign`` invocation
  in the new framework, you can inherit from this template and adjust ``{% block
  manifest_args %}`` and/or ``{% block sign_args %}``.

All hooks are executed with the first argument being the path to temporary
chroot directory, so if you need to run something inside chroot, you should
prefix your command with ``chroot "$1"``, like ``chroot "$1" gramine-manifest
...``. If you don't want to do that (for example, to copy files from outside),
you obviously shouldn't (``cp source "$1"/path/inside/chroot``).

Expected filesystem layout
--------------------------

=============================== ================================================
path                            contents
=============================== ================================================
:file:`/`                       Base system (Debian 12) with gramine installed
                                from packages.
:file:`/app`                    Full contents of the app repository. Also
                                docker's ``WORKDIR``.
:file:`/app/app.manifest{*}`    Gramine Manifest files (``.manifest.template``,
                                ``.manifest`` and ``.manifest.sgx``)
:file:`/usr/local/etc`          Files rendered to
                                :file:`{<project_dir>}/.scag/etc`
=============================== ================================================

Builders
--------

To create a new framework, inherit from `Builder` class, then override:

- `framework` (str)
- `depends` (iterable of strings)
- `extra_files` (dict of str: iterable, str is file path relative to ``.scag/``
  magic directori, and iterable of template names, which are sequentially tried,
  until one is found)

After defining this class, you should add it to entrypoints in
:file:`pyproject.toml`.

Template variables
------------------

``scag.*``
    Dictionary with system-wide, readonly variables. Those can't be overridden
    by user-level variables, nor they should be, as they are e.g., system paths.

``scag.builder``
    Reference to the instance of `Builder`. `Builder` has useful attributes:
    `project_dir`, `magic_dir` (also `variables`, but those are primarily
    available as globals).

``scag.keys_path``
    Path to directory that ships Gramine and Intel release keys. Used in
    ``setup.sh`` hook.

``sgx.*``
    Available as ``sgx.*`` global directory in templates. Used for
    ``sgx.sign_args``.

All values in ``[<framework>]`` section in :file:`scag.toml` are available as
global variables.

Template filters
----------------

``shquote``
    Quotes shell strings (see :py:func:`shlex.quote`). Useful in
    templates.
