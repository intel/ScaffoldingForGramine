# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>

import click.testing
import pytest
from graminescaffolding.__main__ import main

@pytest.fixture
def cli():
    runner = click.testing.CliRunner()
    def cli(*args):
        return runner.invoke(main, args)
    yield cli
