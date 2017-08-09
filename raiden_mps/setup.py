#!/usr/bin/env python3

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as requirements:
    reqs = requirements.read().split()
    config = {
        'packages': [],
        'scripts': [],
        'name': 'rmp-server',
        'install_requires': reqs
    }
    setup(**config)
