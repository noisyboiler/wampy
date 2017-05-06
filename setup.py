from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()


setup(
    name='wampy',
    version='0.9.3',
    description='WAMP RPC and Pub/Sub for python apps and microservices',
    long_description=long_description,
    url='https://github.com/noisyboiler/wampy',
    author='Simon Harrison',
    author_email='noisyboiler@googlemail.com',
    license='GNU GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='WAMP RPC',
    packages=find_packages(),
    install_requires=[
        "eventlet==0.21.0",
    ],
    extras_require={
        'dev': [
            "crossbar==0.15.0",
            "autobahn==0.17.2",
            "pytest==2.9.1",
            "mock==1.3.0",
            "pytest==2.9.1",
            "pytest-capturelog==0.7",
            "colorlog",
            "flake8",
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
