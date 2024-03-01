#!/usr/bin/python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) Wojtek Porczyk <woju@invisiblethingslab.com>

import json
import sys
import textwrap

import click

def _vuln_sort_key(vuln):
    if vuln['id'].startswith('CVE-'):
        return ('CVE', *(int(i) for i in vuln['id'].split('-')[1:]))
    return vuln['id']

@click.command()
@click.argument('file', type=click.File('rb'), default='-')
def main(file):
    data = json.load(file)
    for vuln in sorted(data['vulnerabilities'], key=_vuln_sort_key):
#       print(f'# {vuln=}')
        rating = ' '.join(
            f'{rating["source"]["name"]} {rating["severity"]}/{rating["score"]}'
            for rating in vuln['ratings'])
        print(f'# RATING: {rating}')
        print(f'# AFFECTS:')
        for affects in vuln['affects']:
            print(f'#   {affects["ref"]}')
        print(f'# ADVISORIES:')
        for adv in vuln['advisories']:
            if 'url' in adv:
                print(f'#   {adv["url"]}')
        print(
            f'# DST: https://security-tracker.debian.org/tracker/{vuln["id"]}')
        print(f'# DESCRIPTION:')
        for line in textwrap.wrap(' '.join(vuln['description'].strip().split()),
            width=76,
            break_long_words=False,
            break_on_hyphens=False,
        ):
            print(f'#   {line}')
        print(f'#{vuln["id"]}')
        print()

if __name__ == '__main__':
    main()

# vim: tw=80
