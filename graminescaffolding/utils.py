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

class GramineNumberOptions(GramineStorePrompt):
    def prompt_for_value(self, ctx):
        if not hasattr(self.type, 'choices') or not self.type.choices:
            return super().prompt_for_value(ctx)

        click.echo(f'{self.prompt}')
        for idx, name in enumerate(self.type.choices, 1):
            click.echo(f'{idx} - {name}')

        while True:
            choice = click.prompt('Please provide a number or name')
            try:
                return self.type.choices[int(choice) - 1]
            except ValueError:
                for name in self.type.choices:
                    if name == choice:
                        return name
            except IndexError:
                click.echo('Invalid option. Try Again.')

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

def gramine_option_numerical_prompt(*param_decls, **attrs):
    """
    This decorator enhances the gramine_option_prompt class; for initial guidance,
    consult that orginal class.

    The distinction here lies in the acceptance of prompt options in two formats:
    by name and through a sequence number.
    """
    return click.option(*param_decls, **attrs, cls=GramineNumberOptions)

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
