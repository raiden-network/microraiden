#!/usr/bin/env python3

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as requirements:
    reqs = requirements.read().split()
with open('requirements-dev.txt') as requirements_dev:
    reqs += requirements_dev.read().split()[2:]

config = {
    'packages': [],
    'scripts': [],
    'name': 'microraiden',
    'install_requires': reqs
}
setup(**config)
