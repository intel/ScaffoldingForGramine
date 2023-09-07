# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import click

from ..common.builder import GramineBuilder
from ...utils import gramine_option_prompt

class NodeJSBuilder(GramineBuilder):
    def __init__(self, project_dir, sgx, sgx_key, application):
        super().__init__(project_dir, sgx, sgx_key)
        self.application = application

    def get_framework_name(self):
        return 'nodejs_plain'

    def get_templates_extras_vars(self):
        return {'application': self.application}

    @staticmethod
    def bootstrap_defaults():
        return ['--application=app.js']

    @staticmethod
    def cmdline_setup_parser(project_dir, sgx, sgx_key):
        @click.command()
        @gramine_option_prompt('--application', required=True, type=str,
            prompt="Which script is the main one")
        def click_parser(application):
            return NodeJSBuilder(project_dir, sgx, sgx_key, application)
        return click_parser

def builder_node():
    return NodeJSBuilder
