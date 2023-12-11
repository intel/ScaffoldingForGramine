# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2023 Intel Corporation
#                    Wojtek Porczyk <woju@invisiblethingslab.com>
#                    Mariusz Zaborski <oshogbo@invisiblethingslab.com>
# pylint: disable=too-many-arguments

import functools
import os
import pathlib
import subprocess
import sys
import textwrap
import tomli

import click

#from .frameworks.common.builder import GramineBuilder
from . import (
    builder as _builder,
    client as _client,
    utils,
)
from .utils import (
    GramineExtendedSetupHelp,
    gramine_enable_prompts,
    gramine_list_frameworks,
    gramine_load_framework,
    gramine_option_numerical_prompt,
    gramine_option_prompt,
)

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

def get_docker_run_command(docker_id, *extra_opts):
    return [
        'docker', 'run',
        '--device', '/dev/sgx_enclave',
        '--volume', '/var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket',
        *extra_opts,
        docker_id
    ]

def run_docker(docker_id, *args):
    # pylint: disable=subprocess-run-check
    subprocess.run(get_docker_run_command(docker_id, *args))

def print_docker_usage(docker_id):
    print(f'Your new docker image {docker_id}')
    print('You can run it using command:')
    print(' '.join(get_docker_run_command(docker_id)))

@main.command('quickstart', context_settings={'ignore_unknown_options': True})
@click.pass_context
def quickstart(ctx):
    """
    Quickstart Gramine application using Scaffolding framework.
    """
    # pylint: disable=E1120
    project_dir = gramine_enable_prompts(setup)(standalone_mode=False)
    if not click.confirm('Do you want to build it now?'):
        return
    docker_id = build_step(ctx, project_dir, _builder.SCAG_CONFIG_FILE)
    if not docker_id:
        return
    print_docker_usage(docker_id)
    if not click.confirm('Do you want to run it now?'):
        return
    run_docker(docker_id)

def setup_handle_project_dir(ctx, project_dir, bootstrap):
    def prompt_version(project_dir):
        if not os.path.exists(project_dir):
            if click.confirm('The project directory doesn\'t exist. Do you want '
                'to bootstrap a framework example?'):
                return True
            raise ValueError('Project directory doesn\'t exist, aborting.')

        if not os.path.isdir(project_dir):
            raise ValueError('Project directory has to be a directory.')

        if len(os.listdir(project_dir)) == 0:
            if click.confirm('The project directory seems to be empty. '
                'Do you want to bootstrap the framework example?'):
                return True
        return False

    def cli_version(project_dir, bootstrap):
        if not os.path.exists(project_dir):
            if not bootstrap:
                raise ValueError('The directory doesn\'t exist. Please create a '
                    'directory or use the --bootstrap option.')
            return bootstrap

        if not os.path.isdir(project_dir):
            raise ValueError('The project directory must be a valid directory.')

        if len(os.listdir(project_dir)) != 0 and bootstrap:
            raise ValueError('The project directory must be empty in order to '
                'bootstrap it.')

        return bootstrap

    if getattr(ctx.command, 'prompts_enabled', False):
        return prompt_version(project_dir)
    return cli_version(project_dir, bootstrap)

@main.command('setup', context_settings={'ignore_unknown_options': True},
    cls=GramineExtendedSetupHelp)
@gramine_option_numerical_prompt('--framework', required=True,
    type=click.Choice(gramine_list_frameworks()),
    prompt='Which framework you want to use?',
    help='The framework used by the scaffolded application.')
@gramine_option_prompt('--project_dir', required=True, type=str,
    default=os.getcwd(), prompt='Your\'s app directory is',
    help='The directory of the application to scaffold.')
@gramine_option_prompt('--bootstrap', required=False, is_flag=True,
    default=False, help='Bootstrap directory with framework example.')
@gramine_option_prompt('--passthrough_env', required=False, multiple=True,
    help='List of passthrough environment variables.')
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def setup(ctx, framework, project_dir, bootstrap, passthrough_env, args):
    """
    Build Gramine application using Scaffolding framework.

    Returns:
        str: path to project directory, can be used when standalone_mode is
             set to obj:`False`
    """

    try:
        bootstrap = setup_handle_project_dir(ctx, project_dir, bootstrap)
    except ValueError as err:
        ctx.fail(f'{err}')

    framework = gramine_load_framework(framework)
    parser = framework.cmdline_setup_parser(project_dir, passthrough_env)
    if bootstrap:
        args = framework.bootstrap_defaults
    if getattr(ctx.command, 'prompts_enabled', False):
        parser = utils.gramine_enable_prompts(parser)
    builder = parser(args=args, standalone_mode=False)

    if bootstrap:
        builder.create_example()
    builder.create_config()

    return project_dir

@main.command('build')
@click.option('--conf', default=_builder.SCAG_CONFIG_FILE,
    type=str, # XXX not click.File, this is relative to --project-dir
    help='The filename of the scaffolding configuration file relative to'
        ' --project_dir. This file is most likely generated by scag-setup.')
@click.option('--project_dir', type=click.Path(dir_okay=True, file_okay=False),
    required=True,
    default=os.getcwd(),
    help='The directory of the application to scaffold.')
@click.option('--print-only-image', is_flag=True,
    help='Print only the SHA of the produced docker image, without any'
        ' additional decorators.')
@click.option('--and-run', is_flag=True,
    help='Automatically run the application after build')
@click.pass_context
def build(ctx, project_dir, conf, print_only_image, and_run):
    """
    Build Gramine application using Scaffolding framework.
    """
    docker_id = build_step(ctx, project_dir, conf)
    if docker_id:
        if print_only_image:
            print(docker_id)
        else:
            print_docker_usage(docker_id)

    if and_run:
        run_docker(docker_id)

def build_step(ctx, project_dir, conf):
    """
    Real steps for build Gramine application using Scaffolding framework.
    """
    project_dir = pathlib.Path(project_dir)
    confpath = project_dir / conf
    if not confpath.is_file():
        ctx.fail(f'Configuration file {confpath!r} not found or not a file')

    with open(confpath, 'rb') as file:
        data = tomli.load(file)

    buildertype = gramine_load_framework(data['application']['framework'])
    builder = buildertype(project_dir, data)

    return builder.build()

@main.command('client')
@click.option('--project_dir', '-C', metavar='PATH',
    type=click.Path(dir_okay=True, file_okay=False),
    help='The directory of the scaffolded application. If given,'
        ' scag-client.toml config file will be read from the .scag magic'
        ' subdirectory.')
@click.option('--config', '-f', 'config_file', metavar='FILE',
    type=click.File('r'),
    help='Path to scag-client.toml configuration file.')
@click.option('--request', '-X', 'method', metavar='METHOD', default='GET',
    help='Use another request HTTP method (instead of GET, the default)')
@click.option('--verify',
    type=click.Choice(tuple(_client.VERIFY_CB), case_sensitive=False),
    help='Load RA-TLS library for this method')
@click.option('--output', '-o', metavar='PATH', type=click.File('wb'), default='-',
    help='Output to a file (by default or on "-" writes to standard output)')
@click.option('--mrenclave',
    help='Specify different mrenclave')
@click.option('--mrsigner',
    help='Specify different mrenclave')
@click.option('--allow-debug-enclave-insecure/--no-allow-debug-enclave-insecure',
    help='Allow debug enclave (INSECURE)')
@click.option('--allow-outdated-tcb-insecure/--no-allow-outdated-tcb-insecure',
    help='Allow OUTDATED_TCB (INSECURE)')
@click.argument('url')
@click.pass_context
def client(
    ctx, project_dir, config_file, method, url, verify, output,
    mrenclave,
    mrsigner,
    allow_debug_enclave_insecure,
    allow_outdated_tcb_insecure,
):
    # pylint: disable=too-many-locals,too-many-branches
    if config_file is None:
        if project_dir is not None:
            cfg_path = pathlib.Path(project_dir) / '.scag' / 'scag-client.toml'
        else:
            xdg_config_home = pathlib.Path(os.getenv('XDG_CONFIG_HOME',
                pathlib.Path.home() / '.config'))
            cfg_path = xdg_config_home / 'gramine' / 'scag-client.toml'

        if not cfg_path.is_file():
            ctx.fail('scag-client.toml not found')
        config_file = open(cfg_path, 'rb')

    with config_file:
        config = tomli.load(config_file)

    try:
        verify = verify or config['scag-client']['attestation']
    except LookupError:
        ctx.fail('missing --verify option')

    verify_cb_kwds = {key.replace('-', '_'): value
        for key, value in {
            **config.get('sgx', {}),
            **config.get(verify, {}),
        }.items()
    }

    if mrenclave is not None:
        verify_cb_kwds['mrenclave'] = mrenclave
    if mrsigner is not None:
        verify_cb_kwds['mrsigner'] = mrenclave
    if allow_debug_enclave_insecure is not None:
        verify_cb_kwds['allow_debug_enclave_insecure'] = (
            allow_debug_enclave_insecure)
    if allow_outdated_tcb_insecure is not None:
        verify_cb_kwds['allow_outdated_tcb_insecure'] = (
            allow_outdated_tcb_insecure)

    verify_cb = functools.partial(
        _client.VERIFY_CB[verify.lower()],
        **verify_cb_kwds)

    try:
        resp = _client.request(method, url, verify_cb=verify_cb)
    except _client.AttestationError:
        ctx.fail('attestation failed')
    except TypeError:
        ctx.fail('problem with arguments to the verify function')

    for chunk in iter(functools.partial(resp.read, 4096), b''):
        output.write(chunk)


if __name__ == '__main__':
    main() # pylint: disable=no-value-for-parameter

# vim: tw=80
