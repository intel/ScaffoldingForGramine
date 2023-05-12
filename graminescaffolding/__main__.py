# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>
# pylint: disable=too-many-arguments

import os
import subprocess
import sys
import textwrap
import tomli

import click

from .frameworks.common.builder import GramineBuilder
from .utils import gramine_enable_prompts, gramine_option_prompt

FRAMEWORK_ENTRY_POINTS_GROUP = 'gramine.scaffolding.framework'

# TODO: after python (>= 3.10) simplify this
# NOTE: we can't `try: importlib.metadata`, because the API has changed between 3.9 and 3.10
# (in 3.9 and in backported importlib_metadata entry_points() doesn't accept group argument)
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points # pylint: disable=import-error,no-name-in-module
else:
    from pkg_resources import iter_entry_points as entry_points

def detect(quiet=False):
    """
    Attempt to detect the correct environment.

    Returns:
        bool: :obj:`True` if everything is OK, :obj:`False` otherwise
    """
    try:
        subprocess.run(['is-sgx-available'], capture_output=True, check=True)

    except subprocess.CalledProcessError as exc:
        # returned nonzero, which means some support is missing
        if not quiet:
            click.echo(
                'Missing hardware and/or software support, please fix before '
                'attempting to run any application:', err=True)
            click.echo(textwrap.indent(exc.stdout.decode('ascii'), ' '*4),
                err=True, nl=False)
        return False

    return True

def get_default_sgx_key():
    """
    Get default SGX key path.

    Returns:
        str: path to default SGX key
    """
    return os.path.join(
        os.path.expanduser('~'),
        ".config/gramine/enclave-key.pem",
    )

def list_framework():
    """
    List available frameworks (like python, flask itp.).

    Returns:
        list: list of available frameworks
    """
    # TODO after python (>=3.10): remove disable
    # pylint: disable=unexpected-keyword-arg
    return [entry.name for entry in entry_points(group=FRAMEWORK_ENTRY_POINTS_GROUP)]

def load_framework(name):
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

@click.group()
def main():
    """
    Gramine Scaffolding supercommand.
    """

@main.command('detect')
@click.option('--quiet/--verbose', default=False)
def _detect(quiet):
    """
    Detect runtime environment.
    """
    sys.exit(not detect(quiet=quiet))

def print_docker_usage(docker_id, builder):
    print(f'Your new docker image {docker_id}')
    print('You can run it using command:')
    print(' '.join(builder.get_toolchain().get_run_command(docker_id)))

@main.command('quickstart', context_settings={'ignore_unknown_options': True})
def quickstart():
    """
    Quickstart Gramine application using Scaffolding framework.
    """
    # pylint: disable=E1120
    project_dir = gramine_enable_prompts(setup)(standalone_mode=False)
    if not click.confirm('Do you want to build it now?'):
        return
    docker_id, builder = build_step(project_dir, GramineBuilder.SCAG_CONFIG_FILE,
        get_default_sgx_key())
    if not docker_id:
        return
    print_docker_usage(docker_id, builder)
    if not click.confirm('Do you want to run it now?'):
        return
    builder.get_toolchain().run_docker(docker_id)


@main.command('setup', context_settings={'ignore_unknown_options': True})
@gramine_option_prompt('--framework', required=True,
    type=click.Choice(list_framework()), prompt='Which framework you want to use?',
    help='The framework used by the scaffolded application.')
@gramine_option_prompt('--sgx',
    default=False, type=bool, prompt='Do you want to use SGX?',
    help='Scaffold application using Intel Software Guard Extensions (Intel'
    ' SGX).')
@gramine_option_prompt('--sgx_key', default='', type=str,
    help='Path to the private key used for signing.')
@gramine_option_prompt('--project_dir', required=True, type=str,
    default=os.getcwd(), prompt='Your\'s app directory is',
    help='The directory of the application to scaffold.')
@click.argument('setup_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def setup(ctx, framework, sgx, sgx_key, project_dir, setup_args):
    """
    Build Gramine application using Scaffolding framework.

    Returns:
        str: path to project directory, can be used when standalone_mode is
             set to obj:`False`
    """

    if not os.path.isdir(project_dir):
        print(f'Project dir ({project_dir}) is not a directory')
        sys.exit(1)

    load_framework(framework)().cmdline_setup(
        getattr(ctx.command, 'prompts_enabled', False),
        project_dir, sgx, sgx_key, args=setup_args, standalone_mode=False
    ).generate_config()
    return project_dir

@main.command('build')
@click.option('--conf', default=GramineBuilder.SCAG_CONFIG_FILE,
    required=False, type=str,
    help='The filename of the scaffolding configuration file. This file is'
    ' most likely generated by scag-setup.')
@click.option('--sgx_key', default=get_default_sgx_key(), type=str,
    help='Path to the private key used for signing.')
@click.option('--project_dir', required=True, type=str, default=os.getcwd(),
    help='The directory of the application to scaffold.')
@click.option('--print-only-image', is_flag=True,
    help='Print only the SHA of the produced docker image, without any'
    ' additional decorators.')
def build(project_dir, conf, sgx_key, print_only_image):
    """
    Build Gramine application using Scaffolding framework.
    """
    docker_id, builder = build_step(project_dir, conf, sgx_key)
    if docker_id:
        if print_only_image:
            print(docker_id)
        else:
            print_docker_usage(docker_id, builder)

def build_step(project_dir, filename, sgx_key):
    """
    Real steps for build Gramine application using Scaffolding framework.
    """
    if not os.path.isdir(project_dir):
        print(f'Project dir ({project_dir}) is not a directory')
        sys.exit(1)

    conffile = os.path.join(project_dir, filename)
    if not os.path.isfile(conffile):
        print('Couldn\'t find a configuration file')
        sys.exit(1)

    data = None
    with open(conffile, encoding='utf8') as f_conffile:
        data = tomli.loads(f_conffile.read())

    builder = load_framework(data['application']['framework'])().toml_setup(
        project_dir, sgx_key, data)
    return builder.build(), builder

if __name__ == '__main__':
    main()

# vim: tw=80
