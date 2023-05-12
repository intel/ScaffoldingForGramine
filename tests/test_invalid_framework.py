# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>

def test_invalid_framework(cli):
    result = cli('setup', '--framework', 'INVALID')
    assert result.exit_code != 0
    assert "Invalid value for '--framework'" in result.output
