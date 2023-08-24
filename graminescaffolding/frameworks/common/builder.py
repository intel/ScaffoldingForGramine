# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import os

from abc import abstractmethod

import click
import tomli
import tomli_w

from pkg_resources import resource_listdir, resource_isdir

from ... import templates
from ...utils import gramine_enable_prompts
from .toolchain import get_toolchain

class GramineBuilder:
    GRAMINE_APPLICATION = 'app'
    GRAMINE_MAGIC_DIR = '.scag'
    GRAMINE_MANIFEST = f'{GRAMINE_APPLICATION}.manifest'
    GRAMINE_MANIFEST_TEMPLATE = f'{GRAMINE_MANIFEST}.template'
    SCAG_CONFIG_FILE = 'scag.toml'

    def __init__(self, project_dir, sgx, sgx_key):
        self.project_dir = project_dir
        self.sgx = sgx
        self.sgx_key = sgx_key

    @abstractmethod
    def get_framework_name(self):
        pass

    def get_gramine_manifest(self):
        fname = self.get_framework_name()
        return templates.get_template(f'frameworks/{fname}/{fname}.manifest.template')

    def get_dockerfile_template(self):
        fname = self.get_framework_name()
        return templates.get_template(f'frameworks/{fname}/Dockerfile')

    def get_configuration_template(self):
        fname = self.get_framework_name()
        return templates.get_template(f'frameworks/{fname}/gramine.scaffolding.toml')

    @classmethod
    #pylint: disable=too-many-arguments
    def cmdline_setup(cls, prompts_enabled, bootstrap, project_dir, sgx,
        sgx_key, **kwargs):
        parser = cls.cmdline_setup_parser(project_dir, sgx, sgx_key)
        if bootstrap:
            kwargs['args'] = cls.bootstrap_defaults()
        if prompts_enabled:
            return gramine_enable_prompts(parser)(**kwargs)
        return parser(**kwargs)

    @classmethod
    def cmdline_setup_parser(cls, project_dir, sgx, sgx_key):
        @click.command()
        def click_parser():
            return cls(project_dir, sgx, sgx_key)
        return click_parser

    @classmethod
    def toml_setup(cls, project_dir, sgx_key, data):
        app = data['application']
        return cls(project_dir, app['sgx'], app.get('sgx_key', sgx_key),
            **data[app['framework']])

    def genereate_extra_config_files(self, directory):
        pass

    def get_templates_extras_vars(self):
        return {}

    def get_toolchain(self):
        return get_toolchain(self.sgx, self.sgx_key)

    def build(self):
        toolchain = self.get_toolchain()

        magic_dir = os.path.join(self.project_dir, self.GRAMINE_MAGIC_DIR)
        if not os.path.exists(magic_dir):
            os.makedirs(magic_dir)

        self.genereate_extra_config_files(magic_dir)

        manifest_template = os.path.join(
            magic_dir,
            self.GRAMINE_MANIFEST_TEMPLATE,
        )
        dockerfile = os.path.join(magic_dir, 'Dockerfile')

        with open(manifest_template, 'w', encoding='utf8') as manifest_file:
            manifest_file.write(self.get_gramine_manifest().render())

        with open(dockerfile, 'w', encoding='utf8') as dockerfile_file:
            dockerfile_file.write(self.get_dockerfile_template().render(
                **self.get_templates_extras_vars(),
                manifest=self.GRAMINE_MANIFEST,
                manifest_template=os.path.join(self.GRAMINE_MAGIC_DIR,
                    self.GRAMINE_MANIFEST_TEMPLATE),
                executor=toolchain.get_executor(),
            ))

        return toolchain.generate_docker_image(dockerfile, self.project_dir)

    def generate_config(self):
        filename = os.path.join(self.project_dir, self.SCAG_CONFIG_FILE)
        templ = self.get_configuration_template().render(
            framework=self.get_framework_name(),
            project_dir=self.project_dir,
            sgx=self.sgx,
            sgx_key=self.sgx_key,
            **self.get_templates_extras_vars(),
        )
        # Pack and unpack toml for a nice output
        templ = tomli_w.dumps(tomli.loads(templ))
        with open(filename, 'w', encoding='utf8') as gramine_conf:
            gramine_conf.write(templ)

    def bootstrap_framework_directory(self, curdir):
        jinja_curdir = os.path.join('frameworks', self.get_framework_name(),
            'example', curdir)
        package_curdir = os.path.join('..', '..', 'templates', jinja_curdir)
        project_curdir = os.path.join(self.project_dir, curdir)

        os.makedirs(project_curdir, exist_ok=True)

        for name in resource_listdir(__package__, package_curdir):
            if resource_isdir(__package__, os.path.join(package_curdir, name)):
                self.bootstrap_framework_directory(os.path.join(curdir, name))
                continue

            with open(os.path.join(project_curdir, name), 'w',
                encoding='utf8') as file:
                file.write(
                    templates.get_template(os.path.join(jinja_curdir, name)).render()
                )

    def bootstrap_framework(self):
        return self.bootstrap_framework_directory("")

    @staticmethod
    def bootstrap_defaults():
        return ()
