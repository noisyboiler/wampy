from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()


setup(
    name='wampy',
    version='0.5.0',
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
    entry_points={
        'console_scripts': [
            'wampy=wampy.cli.main:main',
        ],
    },
)
