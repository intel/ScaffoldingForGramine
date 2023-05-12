# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import os

from ..common.builder import GramineBuilder
from ... import templates

class FlaskBuilder(GramineBuilder):
    def __init__(self, project_dir, sgx, sgx_key):
        if not sgx:
            raise ValueError('Flask is supported only with sgx because it requires ra-tls.')
        super().__init__(project_dir, sgx, sgx_key)

    def get_framework_name(self):
        return 'flask'

    def get_configuration_template(self):
        return templates.get_template('gramine.scaffolding.toml')

    def genereate_extra_config_files(self, directory):
        filename = os.path.join(directory, 'nginx.conf')
        with open(filename, 'w', encoding='utf8') as pfile:
            pfile.write(templates.get_template('frameworks/flask/nginx-uwsgi.conf').render())

def builder_flask():
    return FlaskBuilder
