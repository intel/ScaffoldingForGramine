# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import click
import os

from ..common.builder import GramineBuilder
from ...utils import gramine_option_prompt
from ... import templates

class KoaJSBuilder(GramineBuilder):
    def __init__(self, project_dir, sgx, sgx_key, application, koajs_internal_port):
        super().__init__(project_dir, sgx, sgx_key)
        self.application = application
        self.koajs_internal_port = koajs_internal_port

    def get_framework_name(self):
        return 'koajs'

    def get_templates_extras_vars(self):
        return {
            'application': self.application,
            'koajs_internal_port': self.koajs_internal_port
        }

    @staticmethod
    def bootstrap_defaults():
        return ['--application=index.js', '--koajs_internal_port=3000']

    @staticmethod
    def cmdline_setup_parser(project_dir, sgx, sgx_key):
        @click.command()
        @gramine_option_prompt('--application', required=True, type=str,
            prompt="Which script is the main one")
        @gramine_option_prompt('--koajs_internal_port', required=True, type=int,
            prompt="Which port is used by koajs")
        def click_parser(application, koajs_internal_port):
            return KoaJSBuilder(project_dir, sgx, sgx_key, application,
                koajs_internal_port)
        return click_parser

    def genereate_extra_config_files(self, directory):
        filename = os.path.join(directory, 'nginx.conf')
        with open(filename, 'w', encoding='utf8') as pfile:
            pfile.write(templates.get_template('frameworks/koajs/nginx-koajs.conf').render(
                **self.get_templates_extras_vars()))

def builder_koajs():
    return KoaJSBuilder
