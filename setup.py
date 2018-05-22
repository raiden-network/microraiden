#!/usr/bin/env python3

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

import subprocess
import distutils
import os
from setuptools import Command
from setuptools.command.build_py import build_py

DESCRIPTION = 'µRaiden is an off-chain, cheap, scalable and low-latency micropayment solution.'
VERSION = open('microraiden/VERSION', 'r').read().strip()


def read_requirements(path: str):
    assert os.path.isfile(path)
    with open(path) as requirements:
        return requirements.read().split()


def read_version_from_git():
    try:
        import shlex
        git_version, _ = subprocess.Popen(
            shlex.split('git describe --tags'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        git_version = git_version.decode()
        if git_version.startswith('v'):
            git_version = git_version[1:]

        git_version = git_version.strip()
        # if this is has commits after the tag, it's a prerelease:
        if git_version.count('-') == 2:
            _, _, commit = git_version.split('-')
            if commit.startswith('g'):
                commit = commit[1:]
            return '{}+git.r{}'.format(VERSION, commit)
        elif git_version.count('.') == 2:
            return git_version
        else:
            return VERSION
    except BaseException as e:
        print('could not read version from git: {}'.format(e))
        return VERSION


class BuildPyCommand(build_py):
    def run(self):
        self.run_command('compile_webui')
        build_py.run(self)


class CompileWebUI(Command):
    description = 'use npm to compile webui code to raiden/ui/web/dist'
    user_options = [
        ('dev', 'D', 'use development preset, instead of production (default)'),
    ]

    def initialize_options(self):
        self.dev = None

    def finalize_options(self):
        pass

    def run(self):
        npm = distutils.spawn.find_executable('npm')
        if not npm:
            self.announce('NPM not found. Skipping webUI compilation', level=distutils.log.WARN)
            return
        cwd = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'microraiden',
                'webui',
                'microraiden',
            )
        )

        npm_version = subprocess.check_output([npm, '--version'])
        # require npm 4.x.x or later
        if not int(npm_version.decode('utf-8').split('.')[0]) >= 4:
            self.announce(
                'NPM 4.x or later required. Skipping webUI compilation',
                level=distutils.log.WARN,
            )
            return

        command = [npm, 'install']
        self.announce('Running %r in %r' % (command, cwd), level=distutils.log.INFO)
        subprocess.check_call(command, cwd=cwd)

        self.announce('WebUI compiled with success!', level=distutils.log.INFO)


config = {
    'version': read_version_from_git(),
    'scripts': [],
    'name': 'microraiden',
    'author': 'Brainbot Labs Est.',
    'author_email': 'contact@brainbot.li',
    'description': DESCRIPTION,
    'url': 'https://github.com/raiden-network/microraiden/',

    #   With include_package_data set to True command `py setup.py sdist`
    #   fails to include package_data contents in the created package.
    #   I have no idea whether it's a bug or a feature.
    #
    #    'include_package_data': True,

    'license': 'MIT',
    'keywords': 'raiden ethereum microraiden blockchain',
    'install_requires': read_requirements('requirements.txt'),
    'extras_require': {'dev': read_requirements('requirements-dev.txt')},
    'packages': find_packages(exclude=['test']),
    'package_data': {'microraiden': ['data/contracts.json',
                                     'webui/js/*',
                                     'webui/index.html',
                                     'webui/microraiden/dist/umd/microraiden.js',
                                     'VERSION']},
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    'cmdclass': {
        'compile_webui': CompileWebUI,
        'build_py': BuildPyCommand,
    },
}

setup(**config)
