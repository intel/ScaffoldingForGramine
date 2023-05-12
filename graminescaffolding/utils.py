# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import click
import jinja2

templates = jinja2.Environment(loader=jinja2.PackageLoader(__package__))

class GramineStorePrompt(click.Option):
    def __init__(self, *param_decls, **attrs):
        prompt = None
        if 'prompt' in attrs:
            prompt = attrs['prompt']
            del attrs['prompt']

        super().__init__(*param_decls, **attrs)

        self.default_prompt = prompt

    def restore_prompt(self):
        self.prompt = self.default_prompt

def gramine_option_prompt(*param_decls, **attrs):
    """
    This decorator disables the prompt in an option. You can manually enable
    it by calling `gramine_enable_prompts()`. This functionality is helpful
    in controlling interactive functions. For example, suppose we have
    a `setup` function and a `quickstart` function. In that case, the `setup`
    function can be used from the CLI, and the `quickstart` function can
    enable prompts by calling the `setup` function, resulting in an
    interactive version of the setup.
    """
    return click.option(*param_decls, **attrs, cls=GramineStorePrompt)

def gramine_enable_prompts(func):
    """
    This funtion enables prompts declared by gramine_enable_prompts in an
    interactive function.
    """
    func.prompts_enabled = True
    for option in func.params:
        if isinstance(option, GramineStorePrompt):
            option.restore_prompt()
    return func
