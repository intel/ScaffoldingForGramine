# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import tempfile

from abc import abstractmethod

import subprocess

class GramineToolchain:
    @abstractmethod
    def get_executor(self):
        pass

    def generate_docker_image(self, dockerfile, directory):
        with tempfile.NamedTemporaryFile() as tmp:
            self.run(
                'docker', 'build',
                '-f', dockerfile,
                '--iidfile', tmp.name,
                directory,
            )
            # We reopen the file because docker recreates this file
            # with different inode.
            return open(tmp.name, mode="r", encoding='utf8').read()

    def get_run_command(self, docker_id, *extra_opts):
        return [
            'docker', 'run',
            *extra_opts,
            docker_id
        ]

    def run_docker(self, docker_id):
        subprocess.call(self.get_run_command(docker_id))

    def run(self, *opts):
        with subprocess.Popen(
            opts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={
                'DOCKER_BUILDKIT': '1',
            },
        ) as process:
            stdout, stderr = process.communicate()
            if process.wait() != 0:
                print(stdout.decode('utf-8'))
                print(stderr.decode('utf-8'))
                raise RuntimeError(' '.join(opts))

class GramineToolchainSGX(GramineToolchain):
    def __init__(self, sgx_key):
        self.sgx_key = sgx_key

    def get_run_command(self, docker_id, *extra_opts):
        return [
            'docker', 'run',
            '--device', '/dev/sgx_enclave', '--volume',
            '/var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket',
            *extra_opts,
            docker_id
        ]

    def get_executor(self):
        return 'gramine-sgx'

    def generate_docker_image(self, dockerfile, directory):
        with tempfile.NamedTemporaryFile() as tmp:
            self.run(
                'docker', 'build',
                '-f', dockerfile,
                '--secret', f'id=sign,src={self.sgx_key}',
                '--iidfile', tmp.name,
                directory,
            )
            # We reopen the file because docker recreates this file
            # with different inode.
            return open(tmp.name, mode="r", encoding='utf8').read()

class GramineToolchainDirect(GramineToolchain):
    def get_executor(self):
        return 'gramine-direct'

def get_toolchain(sgx, sgx_key):
    if sgx:
        return GramineToolchainSGX(sgx_key)

    return GramineToolchainDirect()
