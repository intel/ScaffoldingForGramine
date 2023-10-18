# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import os
import pathlib
import subprocess
import tarfile
import types

import click
import docker

from . import (
    templates,
    utils,
)

SCAG_MAGIC_DIR = pathlib.Path('.scag')
SCAG_CONFIG_FILE = pathlib.Path('scag.toml')

# render those files, relative to .scag/ magic directory in application directory
WANT_FILES = types.MappingProxyType({
    'app.manifest.template': (
        'frameworks/{framework}/app.manifest.template',
        'app.manifest.template',
    ),
    'sources.list': (
        'frameworks/{framework}/sources.list',
        'sources.list',
    ),

    'mmdebstrap-hooks/setup.sh': (
        'frameworks/{framework}/mmdebstrap-hooks/setup.sh',
        'mmdebstrap-hooks/setup.sh',
    ),
    'mmdebstrap-hooks/customize.sh': (
        'frameworks/{framework}/mmdebstrap-hooks/customize.sh',
        'mmdebstrap-hooks/customize.sh',
    ),

    'Dockerfile': (
        'Dockerfile',
    ),
})

# TODO allow custom, maybe from variables?
CODENAME = 'bookworm'


def get_gramine_dependency():
    try:
        proc = subprocess.run(
            ['dpkg-query', '-W', '-f', '${Package}=${Version}', 'gramine'],
            capture_output=True,
            check=True)
    except subprocess.CalledProcessError:
        raise Exception('dpkg-query failed; is gramine installed?')

    return proc.stdout.decode('ascii')


def extract_mrenclave(file, sigstruct_path='./app/app.sig'):
    with tarfile.open(fileobj=file) as tar:
        try:
            # this might be None if path is in archive but is not a regular file
            sig = tar.extractfile(sigstruct_path)
        except KeyError:
            sig = None
        if sig is None:
            raise Exception(
                f'SIGSTRUCT at {sigstruct_path!r} in the archive not found or '
                f'not a file')
        with sig:
            sig.seek(960)
            return sig.read(32)

# TODO replace SIGSTRUCT, using sgx-sign plugins

class Builder:
    framework = None
    extra_files = types.MappingProxyType({})
    depends = ()
    bootstrap_defaults = ()

    def __init__(self, project_dir, config):

        self.project_dir = pathlib.Path(project_dir)
        self.magic_dir = self.project_dir / SCAG_MAGIC_DIR
        if config['application']['framework'] != self.framework:
            raise ValueError(
                f'expected framework {self.framework!r}, '
                f'found {config["application"]["framework"]!r} in config')
        self.config = config
        self.variables = self.config.get(self.framework,
            types.MappingProxyType({}))
        self.templates = templates.overlay()

        self.templates.globals['scag'] = templates.globals['scag'].copy()
        self.templates.globals['scag'].update({
            'builder': self,
        })
        self.templates.globals['sgx'] = self.config.get('sgx',
            types.MappingProxyType({}))


    def _render_template_to_path(self, template, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        template = self.templates.get_or_select_template(template,
            globals=self.variables)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(template.render())


    def create_config(self):
        # TODO sanity check (parse the file or str in the middle)
        self._render_template_to_path((
            f'frameworks/{self.framework}/scag.toml',
            'scag.toml',
        ), self.project_dir / SCAG_CONFIG_FILE)


    def create_example(self):
        """
        Render the example. Used for bootstrapping.
        """
        prefix = f'frameworks/{self.framework}/example/'
        for template in self.templates.list_templates(
                filter_func=lambda name: name.startswith(prefix)):
            self._render_template_to_path(template,
                self.project_dir / template.removeprefix(prefix))


    def build(self):
        """
        Runs complete build process
        """
        # TODO allow running only some steps
        # TODO split create_chroot, so that between bootstrapping and
        #   gramine-manifest there's branch into docker, so people could
        #   customise the image using dockerfiles, not only hooks to mmdebstrap
        self.render_templates()
        self.create_chroot()
        return self.build_docker_image()


    def render_templates(self):
        """
        Step: create all files in the .scag directory that are rendered from
        templates
        """
        want_files = {}
        want_files.update(WANT_FILES)
        want_files.update(self.extra_files)

        for path, template_names in want_files.items():
            self._render_template_to_path(
                [t.format(framework=self.framework) for t in template_names],
                self.magic_dir / path)


    def create_chroot(self):
        """
        Step: create chroot using mmdebstrap and signs it
        """
        subprocess.run([
            'mmdebstrap',
            '--mode=fakeroot',
            '--include', get_gramine_dependency(),
            *(f'--include={dep}' for dep in self.depends),

            '--setup-hook',
                f'{self.magic_dir / "mmdebstrap-hooks/setup.sh"} "$@"',
            '--customize-hook',
                f'{self.magic_dir / "mmdebstrap-hooks/customize.sh"} "$@"',

            CODENAME,
            self.magic_dir / 'rootfs.tar',
            self.magic_dir / 'sources.list',
        ], check=True)


    def build_docker_image(self):
        """
        Step: create docker image from chroot.tar
        """
        client = docker.from_env()
        image, _ = client.images.build(
            path=os.fspath(self.project_dir),
            dockerfile='.scag/Dockerfile',
            rm=True,
        )
        return image.id


    @classmethod
    def cmdline_setup_parser(cls, project_dir):
        @click.command()
        def click_parser():
            return cls(project_dir, {})
        return click_parser


class PythonBuilder(Builder):
    framework = 'python_plain'
    depends = (
        'python3.11',
    )
    bootstrap_defaults = (
        '--application=hello_world.py',
    )

    @classmethod
    def cmdline_setup_parser(cls, project_dir):
        @click.command()
        @utils.gramine_option_prompt('--application', type=str,
            required=True,
            help="Python application main script.",
            prompt="Which script is the main one")
        def click_parser(application):
            return cls(project_dir, {'application': application})
        return click_parser


class FlaskBuilder(Builder):
    framework = 'flask'
    depends = (
        'nginx',
        'python3-flask',
        'python3.11',
        'uwsgi',
        'uwsgi-plugin-python3',
    )
    extra_files = {
        'nginx.conf': (
            'frameworks/{framework}/nginx-uwsgi.conf',
        ),
    }


class NodejsBuilder(Builder):
    framework = 'nodejs_plain'
    depends = (
        'nodejs',
    )
    bootstrap_defaults = (
        '--application=app.js',
    )

    @classmethod
    def cmdline_setup_parser(cls, project_dir):
        @click.command()
        @utils.gramine_option_prompt('--application', required=True, type=str,
            prompt="Which script is the main one")
        def click_parser(application):
            return cls(project_dir, {'application': application})
        return click_parser


# vim: tw=80
