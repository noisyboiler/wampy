# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    long_description = f.read()


setup(
    name='wampy',
    version='1.0.0',
    description='WAMP RPC and Pub/Sub for python interactive shells, scripts, apps and microservices',  # noqa
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/noisyboiler/wampy',
    author='Simon Harrison',
    author_email='noisyboiler@googlemail.com',
    license='Mozilla Public License 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='WAMP RPC',
    packages=find_packages(),
    install_requires=[
        "attrs==19.2.0",
        "eventlet>=0.24.1",
        "six>=1.11.0",
        "simplejson>=3.11.1",
        "gevent==21.1.2",
    ],
    extras_require={
        'dev': [
            "colorlog>=3.1.4",
            "coverage>=3.7.1",
            "crossbar==20.7.1",
            "flake8>=3.5.0",
            "gevent-websocket>=0.10.1",
            "pytest>=4.0.2",
            "mock>=1.3.0",
            "pytest-capturelog==0.7"
        ],
        'docs': [
            "Sphinx==1.4.5",
            "guzzle_sphinx_theme",
        ],
    },
    entry_points={
        'console_scripts': [
            'wampy=wampy.cli.main:main',
        ],
        # pytest looks up the pytest11 entrypoint to discover its plugins
        'pytest11': [
            'pytest_wampy=wampy.testing.pytest_plugin',
        ]
    },
)
