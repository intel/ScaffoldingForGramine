# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import click

from ..common.builder import GramineBuilder
from ...utils import gramine_option_prompt

class PythonBuilder(GramineBuilder):
    def __init__(self, project_dir, sgx, sgx_key, application):
        super().__init__(project_dir, sgx, sgx_key)
        self.application = application

    def get_framework_name(self):
        return 'python_plain'

    def get_templates_extras_vars(self):
        return {'application': self.application}

    @staticmethod
    def cmdline_setup_parser(project_dir, sgx, sgx_key):
        @click.command()
        @gramine_option_prompt('--application', required=True, type=str,
            help="Python application main script.",
            prompt="Which script is the main one")
        def click_parser(application):
            return PythonBuilder(project_dir, sgx, sgx_key, application)
        return click_parser

def builder_python():
    return PythonBuilder
