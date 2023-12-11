Deployment guidelines
=====================

Re-signing SIGSTRUCT
--------------------

If you need to sign the enclave with another ("production") key after the
application was scaffolded, you can extract SIGSTRUCT from the
:file:`rootfs.tar` file, which is an intermediate artifact, from which the
container is built. The :file:`rootfs.tar` file can be found in :file:`.scag`
subdirectory of the project after :ref:`scag-build <scag-build>` finishes.
SIGSTRUCT is located in :file:`./app/app.sig` inside the tarball (and in
:file:`/app/app.sig` inside the container).

Instead of delivering the container to Ops, developer should deliver
:file:`rootfs.tar` and :file:`Dockerfile` from :file:`.scag/`. Ops people would
then:

1. Extract the SIGSTRUCT from the tarball:

   .. code-block:: sh

        tar -xf .scag/rootfs.tar ./app/app.sig

   This command will create :file:`app/` directory (if it does not exist) and
   unpack the SIGSTRUCT to :file:`app.sig` in this directory.

2. Sign the SIGSTRUCT again. This step depends on the exact tooling and is not
   described in this document. After signing, replace :file:`./app/app.sig` with
   newly signed structure.

3. Replace the file in the :file:`rootfs.tar`:

   .. code-block:: sh

        tar -rf .scag/rootfs.tar ./app/app.sig

4. Rebuild the container image:

   .. code-block:: sh

        docker build . -f .scag/Dockerfile

   This container may now be deployed as usual.
