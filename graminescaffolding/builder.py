# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>
#                    Rafał Wojdyła <omeg@invisiblethingslab.com>

import json
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

    'Dockerfile-final': (
        'Dockerfile-final',
    ),

    '.dockerignore': (
        '.dockerignore',
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

def extract_mrenclave_from_bytes(sigstruct):
    return sigstruct[960:960+32]

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
    extra_run_args = ()
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

        self._docker_client = None

    @property
    def docker(self):
        if self._docker_client is None:
            self._docker_client = docker.from_env()
        return self._docker_client


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
            'MAGIC_DIR': SCAG_MAGIC_DIR,
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
        self.render_templates()
        self.create_chroot()
        image_unsigned = self.build_docker_image()
        image, mrenclave = self.sign_docker_image(image_unsigned)
        self.render_client_config(mrenclave)
        return image.id


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
        Step: create chroot using mmdebstrap
        """

        # XXX: we probably want a force flag to rebuild rootfs
        if os.path.isfile(self.rootfs_tar):
            return

        subprocess.run([
            'mmdebstrap',
            '--mode=unshare',
            '--keyring', utils.KEYS_PATH / 'trusted.gpg.d',
            '--include', get_gramine_dependency(),
            '--setup-hook',
                f'sh {self.magic_dir / "mmdebstrap-hooks/setup.sh"} "$@"',
            '--customize-hook',
                f'sh {self.magic_dir / "mmdebstrap-hooks/customize.sh"} "$@"',

            CODENAME,
            self.rootfs_tar,
            self.magic_dir / 'sources.list',
        ], check=True)


    def sign_chroot(self, rootdir, manifest_path='app/app.manifest'):
        """
        Signs tarball of the system image. Manifest needs to be in
        /app/app.manifest

        Args:
            file: file object of the tarball
            manifest_path (str): path to manifest inside the tarball

        Returns:
            (bytes, bytes): Tuple of file contents ``(app.manifest.sgx,
            app.sig)`` that need to be added into the final image. MRENCLAVE can
            be extracted from the latter.
        """
        with tempfile.TemporaryDirectory() as tmpsigdir:
            tmpsigdir = pathlib.Path(tmpsigdir)

            tmpmsgx = tmpsigdir / 'app.manifest.sgx'
            tmpsig = tmpsigdir / 'app.sig'

            subprocess.run([
                'gramine-sgx-sign',
                '--date', '0000-00-00',
                *self.config.get('sgx', {}).get('sign_args', []),
                '--chroot', rootdir,
                '--manifest', rootdir / manifest_path,
                '--output', tmpmsgx,
                '--sigfile', tmpsig,
            ], check=True)

            return (tmpmsgx.read_bytes(), tmpsig.read_bytes())


    def sign_docker_image(self, image):
        with (
            tempfile.TemporaryFile() as savefile,
            tempfile.TemporaryDirectory() as tmprootdir,
        ):
            tmprootdir = pathlib.Path(tmprootdir)

            for chunk in image.save():
                savefile.write(chunk)
            savefile.seek(0)

            with tarfile.open(fileobj=savefile) as tar:
                manifest = json.load(tar.extractfile('manifest.json'))

                # assert we have only 1 image
                m_image, = manifest

                for layer_path in m_image['Layers']:
                    with tarfile.open(
                        fileobj=tar.extractfile(layer_path)
                    ) as layer_tar:
                        # Filter out special files, because those can't be
                        # mknod()ed if we're not root. We don't care, no-one
                        # should be measuring them.
                        # TODO after Python 12: use extractall(filter=)
                        members = layer_tar.getmembers()
                        members = [ti for ti in members if not ti.isdev()]
                        layer_tar.extractall(tmprootdir, members=members)

                msgx, sig = self.sign_chroot(tmprootdir)

        (self.magic_dir / 'app.manifest.sgx').write_bytes(msgx)
        (self.magic_dir / 'app.sig').write_bytes(sig)
        image2 = self.build_docker_image(
            dockerfile='.scag/Dockerfile-final',
            buildargs={'FROM': image.id},
        )

        mrenclave = extract_mrenclave_from_bytes(sig).hex()
        return image2, mrenclave


    def build_docker_image(self, dockerfile='.scag/Dockerfile', **kwds):
        """
        Step: create docker image from chroot.tar
        """
        kwds.setdefault('rm', True)

        image, _ = self.docker.images.build(
            path=os.fspath(self.project_dir),
            dockerfile=dockerfile,
            **kwds,
        )
        return image


    def get_docker_run_cmd(self, docker_id):
        return [
            'docker', 'run',
            '--device', '/dev/sgx_enclave',
            '--volume', '/var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket',
            *self.extra_run_args,
            docker_id,
        ]


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
    extra_run_args = (
        '--publish', '8080:8080',
    )


class NodejsBuilder(Builder):
    framework = 'nodejs_plain'
    depends = (
        'nodejs',
    )
    bootstrap_defaults = (
        '--application=app.js',
    )
    extra_run_args = (
        '--publish', '8080:8080',
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
    )
    extra_files = {
        'etc/nginx.conf': (
            'frameworks/nginx/nginx.conf',
        ),
    }

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


class KoajsBuilder(Builder):
    framework = 'koajs'
    depends = (
        'nodejs',
        'npm',
        'nginx',
    )
    bootstrap_defaults = (
        '--application=index.js',
    )
    extra_files = {
        'etc/nginx.conf': (
            'frameworks/nginx/nginx.conf',
        ),
    }
    extra_run_args = (
        '--publish', '8080:8080',
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


class JavaJARBuilder(Builder):
    framework = 'java_jar'
    depends = (
        'openjdk-17-jre-headless',
    )
    bootstrap_defaults = (
        '--application=hello_world.jar',
    )
    extra_run_args = (
        '--publish', '8080:8080',
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
    extra_run_args = (
        '--publish', '8080:8080',
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
    extra_run_args = (
        '--publish', '8080:8080',
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
