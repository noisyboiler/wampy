from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()


setup(
    name='wampy',
    version='0.7.8',
    description='WAMP RPC and Pub/Sub for python apps and microservices',
    long_description=long_description,
    url='https://github.com/noisyboiler/wampy',
    author='Simon Harrison',
    author_email='noisyboiler@googlemail.com',
    license='GNU GPLv3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='WAMP RPC',
    packages=find_packages(),
    install_requires=[
        "eventlet==0.18.4",
    ],
    extras_require={
        'dev': [
            "crossbar==0.15.0",
            "pytest==2.9.1",
            "mock==1.3.0",
            "pytest-capturelog",
            "colorlog",
            "flake8",
        ]
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
