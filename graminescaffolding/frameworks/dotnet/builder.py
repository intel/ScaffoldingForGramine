# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>
#                    Rafał Wojdyła <omeg@invisiblethingslab.com>

import click

from ..common.builder import GramineBuilder
from ...utils import gramine_option_prompt

class DotnetBuilder(GramineBuilder):
    # pylint: disable=too-many-arguments
    def __init__(self, project_dir, sgx, sgx_key, build_config, project_file, target):
        super().__init__(project_dir, sgx, sgx_key)
        self.build_config = build_config
        self.project_file = project_file
        self.target = target

    def get_framework_name(self):
        return 'dotnet'

    def get_templates_extras_vars(self):
        return {'build_config': self.build_config, 'project_file': self.project_file,
                'target': self.target}

    @staticmethod
    def bootstrap_defaults():
        return ['--build_config=Release', '--project_file=hello_world.csproj',
                '--target=hello_world']

    @staticmethod
    def cmdline_setup_parser(project_dir, sgx, sgx_key):
        @click.command()
        @gramine_option_prompt('--build_config', required=True,
            type=click.Choice(['Debug', 'Release']),
            help='Build configuration', prompt='Build configuration')
        @gramine_option_prompt('--project_file', required=True, type=str,
            help='Application\'s main project file',
            prompt='Application\'s main project file')
        @gramine_option_prompt('--target', required=True, type=str,
            help='Application binary (found in bin/{Debug|Release}/net7.0)',
            prompt='Application binary (found in bin/{Debug|Release}/net7.0)')
        def click_parser(build_config, project_file, target):
            return DotnetBuilder(project_dir, sgx, sgx_key, build_config, project_file, target)
        return click_parser

def builder_dotnet():
    return DotnetBuilder
