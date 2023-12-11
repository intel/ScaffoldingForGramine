# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>

import pathlib
import shlex
import sys
import os

import click
import jinja2

KEYS_PATH = pathlib.Path(__file__).parent / 'keys'

templates = jinja2.Environment(
    loader=jinja2.PackageLoader(__package__),
    undefined=jinja2.StrictUndefined,
    keep_trailing_newline=True,
)
templates.globals['scag'] = {
    'keys_path': KEYS_PATH,
}

def filter_shquote(s):
    return shlex.quote(os.fspath(s))
templates.filters['shquote'] = filter_shquote

FRAMEWORK_ENTRY_POINTS_GROUP = 'gramine.scaffolding.framework'

# TODO: after python (>= 3.10) simplify this
# NOTE: we can't `try: importlib.metadata`, because the API has changed between 3.9 and 3.10
# (in 3.9 and in backported importlib_metadata entry_points() doesn't accept group argument)
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points # pylint: disable=import-error,no-name-in-module
else:
    from pkg_resources import iter_entry_points as entry_points

def gramine_list_frameworks():
    """
    List available frameworks (like python, flask itp.).

    Returns:
        list: list of available frameworks
    """
    # TODO after python (>=3.10): remove disable
    # pylint: disable=unexpected-keyword-arg
    return sorted([
        entry.name for entry in entry_points(group=FRAMEWORK_ENTRY_POINTS_GROUP)
    ])

def gramine_load_framework(name):
    """
    Load framework by name.

    Returns:
        class: framework class
    """
    # TODO after python (>=3.10): remove disable
    # pylint: disable=unexpected-keyword-arg
    for entry in entry_points(group=FRAMEWORK_ENTRY_POINTS_GROUP):
        if entry.name == name:
            return entry.load()
    raise KeyError(name)

class GramineExtendedSetupHelpFormatter(click.HelpFormatter):
    def write_dl(self, rows, col_max=30, col_spacing=2):
        super().write_dl(rows, col_max, col_spacing)

        self.dedent()
        self.write_heading('\nFramework specific options')

        for name in gramine_list_frameworks():
            parser = gramine_load_framework(name).cmdline_setup_parser(
                None, None)
            self.indent()
            opts = []
            for param in parser.params:
                if isinstance(param, click.Option):
                    helptxt = param.help
                    if helptxt is None:
                        helptxt = ''
                    if param and getattr(param, "required", False):
                        helptxt += ' [required]'
                    opts.append((param.opts[0], helptxt))

            self.write_text(f'# {name}:\n')
            self.indent()
            if opts:
                super().write_dl(opts, col_max, 5)
            else:
                self.write_text('N/A')
            self.dedent()
            self.dedent()
            self.write_text('\n')

class GramineExtendedSetupHelp(click.Command):
    def get_help(self, ctx):
        formatter = GramineExtendedSetupHelpFormatter(width=ctx.max_content_width)
        self.format_help(ctx, formatter)
        return formatter.getvalue().rstrip('\n')

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
