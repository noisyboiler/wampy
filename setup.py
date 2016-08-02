from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()


setup(
    name='wampy',
    version='0.3.0',
    description='WAMP RPC and Pub/Sub for stand alone clients and microservices',
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
        "crossbar==0.13.0",
        "eventlet==0.18.4",
    ],
)
