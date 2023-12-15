# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>
#                    Rafał Wojdyła <omeg@invisiblethingslab.com>

import os
import pathlib
import shlex
import subprocess
import tarfile
import tempfile
import types

import importlib.resources

import click
import docker
import jinja2

from . import (
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


_templates = jinja2.Environment(
    loader=jinja2.PackageLoader(__package__),
    undefined=jinja2.StrictUndefined,
    keep_trailing_newline=True,
)
_templates.globals['scag'] = {
    'keys_path': utils.KEYS_PATH,
}

def filter_shquote(s):
    return shlex.quote(os.fspath(s))
_templates.filters['shquote'] = filter_shquote


def get_gramine_dependency():
    try:
        proc = subprocess.run(
            ['dpkg-query', '-W', '-f', '${Package}=${Version}', 'gramine'],
            capture_output=True,
            check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError('dpkg-query failed; is gramine installed?')

    return proc.stdout.decode('ascii')


def _extract_mrenclave_from_file(file):
    file.seek(960)
    return file.read(32)

def extract_mrenclave_from_tar(file, sigstruct_path='./app/app.sig'):
    with tarfile.open(fileobj=file) as tar:
        try:
            # this might be None if path is in archive but is not a regular file
            sig = tar.extractfile(sigstruct_path)
        except KeyError:
            sig = None
        if sig is None:
            raise ValueError(
                f'SIGSTRUCT at {sigstruct_path!r} in the archive not found or '
                f'not a file')
        with sig:
            return _extract_mrenclave_from_file(sig)

def extract_mrenclave_from_path(path):
    with open(path, 'rb') as file:
        return _extract_mrenclave_from_file(file)

# TODO replace SIGSTRUCT, using sgx-sign plugins

class Builder:
    framework = None
    extra_files = types.MappingProxyType({})
    depends = ()
    bootstrap_defaults = ()
    BINARY_EXT = (
        '.jar',
    )
    extra_templates_path = None

    def __init__(self, project_dir, config):
        self.project_dir = pathlib.Path(project_dir)
        self.magic_dir = self.project_dir / SCAG_MAGIC_DIR
        self.rootfs_tar = self.magic_dir / 'rootfs.tar'
        if config['application']['framework'] != self.framework:
            raise ValueError(
                f'expected framework {self.framework!r}, '
                f'found {config["application"]["framework"]!r} in config')
        self.config = config
        self.variables = self.config.get(self.framework,
            types.MappingProxyType({}))
        self.templates = self._init_jinja_env()


    def _init_jinja_env(self):
        loaders = [jinja2.PrefixLoader({'': _templates.loader}, '!')]
        conf_templates = self.config['application'].get('templates')
        if conf_templates is not None:
            loaders.append(jinja2.FileSystemLoader(
                self.project_dir / conf_templates))
        if self.extra_templates_path is not None:
            loaders.append(jinja2.FileSystemLoader(
                self.project_dir / self.extra_templates_path))
        loaders.append(_templates.loader)

        templates = _templates.overlay(loader=jinja2.ChoiceLoader(loaders))

        templates.globals['scag'] = _templates.globals['scag'].copy()
        templates.globals['scag'].update({
            'builder': self,
        })
        templates.globals['sgx'] = self.config.get('sgx',
            types.MappingProxyType({}))
        templates.globals['passthrough_env'] = list(
            self.config['gramine'].get('passthrough_env', []))

        return templates


    def _render_template_to_path(self, template, path, /, **kwds):
        path.parent.mkdir(parents=True, exist_ok=True)
        template = self.templates.get_or_select_template(template,
            globals=self.variables)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(template.render(**kwds))


    def _copy_binary_template_to_path(self, template, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        package, resource = template.rsplit('/', 1)
        package = package.replace('/', '.')

        data = importlib.resources.read_binary(f'{__package__}.{package}',
            resource)
        with open(path, 'wb') as file:
            file.write(data)


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
            dest = self.project_dir / template.removeprefix(prefix)
            if template.endswith(self.BINARY_EXT):
                self._copy_binary_template_to_path(f'templates/{template}',
                    dest)
            else:
                self._render_template_to_path(template, dest)


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
        mrenclave = self.sign_chroot()
        self.render_client_config(mrenclave)
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


    def render_client_config(self, mrenclave):
        self._render_template_to_path(
            'scag-client.toml',
            self.magic_dir / 'scag-client.toml',
            mrenclave=mrenclave)


    def create_chroot(self):
        """
        Step: create chroot using mmdebstrap and signs it
        """
        subprocess.run([
            'mmdebstrap',
            '--mode=unshare',
            '--keyring', utils.KEYS_PATH / 'trusted.gpg.d',
            '--include', get_gramine_dependency(),
            *(f'--include={dep}' for dep in self.depends),

            '--setup-hook',
                f'sh {self.magic_dir / "mmdebstrap-hooks/setup.sh"} "$@"',
            '--customize-hook',
                f'sh {self.magic_dir / "mmdebstrap-hooks/customize.sh"} "$@"',

            CODENAME,
            self.rootfs_tar,
            self.magic_dir / 'sources.list',
        ], check=True)


    def sign_chroot(self):
        with (
            tempfile.TemporaryDirectory() as tmprootdir,
            tempfile.TemporaryDirectory() as tmpsigdir,
        ):
            tmprootdir = pathlib.Path(tmprootdir)
            tmpsigdir = pathlib.Path(tmpsigdir)

            tmpmsgx = tmpsigdir / 'app.manifest.sgx'
            tmpsig = tmpsigdir / 'app.sig'

            with tarfile.open(self.rootfs_tar) as tar:
                # Filter out special files, because those can't be mknod()ed
                # if we're not root. We don't care, no-one should be
                # measuring them.
                # TODO after Python 12: use extractall(filter=)
                members = tar.getmembers()
                members = [ti for ti in members if not ti.isdev()]
                tar.extractall(tmprootdir, members=members)

            subprocess.run([
                'gramine-sgx-sign',
                '--date', '0000-00-00',
                *self.config.get('sgx', {}).get('sign_args', []),
                '--chroot', tmprootdir,
                '--manifest', tmprootdir / 'app/app.manifest',
                '--output', tmpmsgx,
                '--sigfile', tmpsig,
            ], check=True)

            with tarfile.open(self.rootfs_tar, 'a') as tar:
                for path in [tmpmsgx, tmpsig]:
                    tar.add(path, arcname=f'app/{path.name}')

            return extract_mrenclave_from_path(tmpsig).hex()


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
    def cmdline_setup_parser(cls, project_dir, passthrough_env):
        @click.command()
        def click_parser():
            return cls(project_dir, {
                'application': {
                    'framework': cls.framework,
                },
                'gramine': {
                    'passthrough_env': passthrough_env,
                },
            })
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
    def cmdline_setup_parser(cls, project_dir, passthrough_env):
        @click.command()
        @utils.gramine_option_prompt('--application', type=str,
            required=True,
            help="Python application main script.",
            prompt="Which script is the main one")
        def click_parser(application):
            return cls(project_dir, {
                'application': {
                    'framework': cls.framework,
                },
                'gramine': {
                    'passthrough_env': passthrough_env,
                },
                cls.framework: {
                    'application': application,
                },
            })
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
        'etc/nginx.conf': (
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
    def cmdline_setup_parser(cls, project_dir, passthrough_env):
        @click.command()
        @utils.gramine_option_prompt('--application', required=True, type=str,
            prompt="Which script is the main one")
        def click_parser(application):
            return cls(project_dir, {
                'application': {
                    'framework': cls.framework,
                },
                'gramine': {
                    'passthrough_env': passthrough_env,
                },
                cls.framework: {
                    'application': application,
                },
            })
        return click_parser


class ExpressjsBuilder(Builder):
    framework = 'expressjs'
    depends = (
        'nodejs',
        'npm',
        'nginx',
    )
    bootstrap_defaults = (
        '--application=index.js',
        '--expressjs_internal_port=3000',
    )
    extra_files = {
        'etc/nginx.conf': (
            'frameworks/{framework}/nginx-expressjs.conf',
        ),
    }

    @classmethod
    def cmdline_setup_parser(cls, project_dir, passthrough_env):
        @click.command()
        @utils.gramine_option_prompt('--application', required=True, type=str,
            prompt="Which script is the main one")
        @utils.gramine_option_prompt('--expressjs_internal_port', required=True,
            type=int, prompt="Which port is used by expressjs")
        def click_parser(application, expressjs_internal_port):
            return cls(project_dir, {
                'application': {
                    'framework': cls.framework,
                },
                'gramine': {
                    'passthrough_env': passthrough_env,
                },
                cls.framework: {
                    'application': application,
                    'expressjs_internal_port': expressjs_internal_port,
                },
            })
        return click_parser


class KoajsBuilder(Builder):
    framework = 'koajs'
    depends = (
        'nodejs',
        'npm',
        'nginx',
    )
    bootstrap_defaults = (
        '--application=index.js',
        '--koajs_internal_port=3000',
    )
    extra_files = {
        'etc/nginx.conf': (
            'frameworks/{framework}/nginx-koajs.conf',
        ),
    }

    @classmethod
    def cmdline_setup_parser(cls, project_dir, passthrough_env):
        @click.command()
        @utils.gramine_option_prompt('--application', required=True, type=str,
            prompt="Which script is the main one")
        @utils.gramine_option_prompt('--koajs_internal_port', required=True,
            type=int, prompt="Which port is used by koajs")
        def click_parser(application, koajs_internal_port):
            return cls(project_dir, {
                'application': {
                    'framework': cls.framework,
                },
                'gramine': {
                    'passthrough_env': passthrough_env,
                },
                cls.framework: {
                    'application': application,
                    'koajs_internal_port': koajs_internal_port,
                },
            })
        return click_parser


class JavaJARBuilder(Builder):
    framework = 'java_jar'
    depends = (
        'openjdk-17-jre-headless',
    )
    bootstrap_defaults = (
        '--application=hello_world.jar',
    )

    @classmethod
    def cmdline_setup_parser(cls, project_dir, passthrough_env):
        @click.command()
        @utils.gramine_option_prompt('--application', required=True, type=str,
            prompt="Which JAR is the main one")
        def click_parser(application):
            return cls(project_dir, {
                'application': {
                    'framework': cls.framework,
                },
                'gramine': {
                    'passthrough_env': passthrough_env,
                },
                cls.framework: {
                    'application': application,
                },
            })
        return click_parser


class JavaGradleBuilder(Builder):
    framework = 'java_gradle'
    depends = (
        'gradle',
        'openjdk-17-jdk',
        'openjdk-17-jre-headless',
    )
    bootstrap_defaults = (
        '--application=build/libs/hello_world.jar',
    )

    @classmethod
    def cmdline_setup_parser(cls, project_dir, passthrough_env):
        @click.command()
        @utils.gramine_option_prompt('--application', required=True, type=str,
            prompt="Which JAR is the main one")
        def click_parser(application):
            return cls(project_dir, {
                'application': {
                    'framework': cls.framework,
                },
                'gramine': {
                    'passthrough_env': passthrough_env,
                },
                cls.framework: {
                    'application': application,
                },
            })
        return click_parser


class DotnetBuilder(Builder):
    framework = 'dotnet'
    depends = (
        'dotnet-sdk-7.0',
        'ca-certificates',
    )
    bootstrap_defaults = (
        '--build_config=Release',
        '--project_file=hello_world.csproj',
        '--target=hello_world',
    )

    @classmethod
    def cmdline_setup_parser(cls, project_dir, passthrough_env):
        @click.command()
        @utils.gramine_option_prompt('--build_config', required=True,
            type=click.Choice(['Debug', 'Release']),
            help='Build configuration', prompt='Build configuration')
        @utils.gramine_option_prompt('--project_file', required=True, type=str,
            help='Application\'s main project file',
            prompt='Application\'s main project file')
        @utils.gramine_option_prompt('--target', required=True, type=str,
            help='Application binary (found in bin/{Debug|Release}/net7.0)',
            prompt='Application binary (found in bin/{Debug|Release}/net7.0)')
        def click_parser(build_config, project_file, target):
            return cls(project_dir, {
                'application': {
                    'framework': cls.framework,
                },
                'gramine': {
                    'passthrough_env': passthrough_env,
                },
                cls.framework: {
                    'build_config': build_config,
                    'project_file': project_file,
                    'target': target,
                },
            })
        return click_parser


# vim: tw=80
