#!/usr/bin/env python3

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as requirements:
    reqs = requirements.read().split()

config = {
    'packages': ['client'],
    'scripts': [],
    'name': 'm2mclient',
    'install_requires': reqs
}

setup(**config)
