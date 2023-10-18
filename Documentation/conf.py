import os
import sys
sys.path.insert(0, os.path.abspath('.'))

project = 'Gramine Scaffolding'
copyright = '2023, Wojtek Porczyk'
author = 'Wojtek Porczyk'
_man_pages_author = 'Wojtek Porczyk'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
]

exclude_patterns = ['_build', '.gitignore']

# TODO after Debian 12: furo
html_theme = 'sphinx_rtd_theme'
extensions += ['sphinx_rtd_theme']

man_pages = [
    ('manpages/scag-build', 'scag-build', 'Build Gramine Scaffolding application', _man_pages_author, 1),
    ('manpages/scag-detect', 'scag-detect', 'Scaffolding autodetector', _man_pages_author, 1),
    ('manpages/scag-quickstart', 'scag-quickstart', 'Build Gramine Scaffolding application', _man_pages_author, 1),
    ('manpages/scag-setup', 'scag-setup', 'Build Gramine Scaffolding application', _man_pages_author, 1),
]

interspinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}
