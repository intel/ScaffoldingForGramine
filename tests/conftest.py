# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>

import pathlib
import shutil

import click.testing
import docker
import pytest

from graminescaffolding.__main__ import main

@pytest.fixture
def cli():
    runner = click.testing.CliRunner()
    def cli(*args):
        return runner.invoke(main, args)
    yield cli

@pytest.fixture
def docker_run():
    client = docker.from_env()
    def docker_run(*args, **kwds):
        kwds.setdefault('detach', False)
        kwds.setdefault('devices', ['/dev/sgx_enclave'])
        kwds.setdefault('remove', True)
        kwds.setdefault('tty', True)
        kwds.setdefault('volumes',
            ['/var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket'])
        return client.containers.run(*args, **kwds)

    try:
        yield docker_run
    finally:
        client.close()

@pytest.fixture
def project_dir(request):
    ret = (pathlib.Path(request.fspath).parent
        / f'app-{request.node.name.removeprefix("test_")}')
    if ret.exists():
        shutil.rmtree(ret)
    return ret

@pytest.fixture
def get_image_id():
    def get_image_id(result):
        image_id = result.output.strip()
        assert image_id.startswith('sha256:')
        assert set(image_id.removeprefix('sha256:').casefold()).issubset('0123456789abcdef')
        return image_id
    return get_image_id
