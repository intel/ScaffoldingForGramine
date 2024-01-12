Templates
=========

Introduction
------------

SCAG works by rendering certain files from Jinja templates, then processing the
resulting directory (containing both user's application and mentioned
renderings) into system image, measuring and signing it, and last but not least,
packaging everything into docker (OCI) container.

If you need to customise some of those files, it might be that you need to
override templates from which they are rendered.

For more complicated applications (e.g. those that have or had their own
Dockerfiles with significant logic), there might be need to do some
postprocessing on docker images after copying in the build artifacts. In SCAG
this is done by overriding templates that get rendered into configuration files
such as Dockerfile or Gramine manifest. This guide will show how to override the
Dockerfile for ``python-plain`` framework's helloworld example.

What templates are rendered for a particular app is defined by the framework,
but there are some templates common to all frameworks, like ``Dockerfile`` or
``app.manifest.template``. If you need to override a template specific to
a framework, unfortunately you need to look into SCAG source to find the exact
template name.

SCAG uses `Jinja <https://jinja.palletsprojects.com/>`__ templates. Introducion
of this template language is outside of scope for this document, which will
only describe concepts needed to explain, how SCAG uses those templates.

Template names, paths and inheritance
-------------------------------------

In Jinja, templates have names, which usually translate to filenames under some
preconfigured directory (though not always and not directly). An example name
would be ``Dockerfile`` or ``framework/python-flask/app.manifest.template``. To
override a template, you need to know it's name beforehand. In SCAG, default
templates are stored in :file:`{platlib}/graminescaffolding/templates` (on
Debian-derived system it might be
:file:`/usr/lib/python3/dist-packages/graminescaffolding/templates`). You should
not change the default templates, your changes will be lost when SCAG is
updated.

To define your own templates, you need to specify your own directory with
templates (usually :file:`templates/` subdirectory of your project directory)
and provide it's name in ``application.templates`` setting in :file:`scag.toml`.
Example from bootstrap contains this line commented, so you probably need to
uncomment it and ``mkdir`` this directory.

Templates, which are present in project's ``templates/`` override completely
templates that have the same name (i.e. are under the same subpath in default
directory). You need to either provide all the template content (even the parts
that you don't need to change), or you can *inherit* from one of the default
templates. If you need to inherit template that has the same name, in SCAG you
can add ``!`` character to the template name in ``{% extends %}`` statement:

.. code-block:: jinja

    {% extends '!Dockerfile %}

Just writing ``{% extends 'Dockerfile' %}`` (without ``!``) is an error, because
it causes recursion in inheritance resolution.

When you are inheriting from existing template, you can override any number of
blocks. Read the original template to see what you can change there. Previous
contents of the block are available as ``{{ super() }}``.

Choosing the template to override
---------------------------------

Here's a non-exhaustive list
of files used by SCAG and templates from which they are rendered (and which we
will be overriding):

- File ``.scag/Dockerfile`` is responsible of creating initial (not signed)
  image. Rendered from ``Dockerfile`` template.

- File ``.scag/Dockerfile-final`` is responsible for replacing
  ``app.manifest.sgx`` and ``app.sig`` (SIGSTRUCT) inside the container.
  Rendered from ``Dockerfile-final``. It is not advisable to overrider this
  template.

- File ``.scag/app.manifest.template``, which ends up in the container as
  ``/app/app.manifest.template``. Rendered from either
  ``frameworks/<framework>/app.manifest.template`` or (if that template is not
  provided by framework), then ``app.manifest.template``. This is the Gramine
  manifest template.

  .. important::

      You need to know if the framework uses it's own manifest template, because
      if it does, you need to override the framework-specific template.
      Overriding global template won't work.

Example
-------

The following file can be placed in ``template/Dockerfile`` to change the
message printed by ``hello_world.py`` script in demo app from ``python_plain``:

.. code-block:: jinja

    {% extends '!Dockerfile' %}

    {% block local %}
    RUN sed -i -e s/world/asdfg/ /app/hello_world.py
    {% endblock %}
