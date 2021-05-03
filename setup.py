#!/usr/bin/env python

import sys, os
from glob import glob

# Install setuptools if it isn't available:
try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from distutils.command.install_headers import install_headers
from setuptools import find_packages
from setuptools import setup

NAME =               'processor_component'
VERSION =            '0.3.0'
AUTHOR =             'Adam Tomkins, Nikul Ukani, Yiyin Zhou'
AUTHOR_EMAIL =       'a.tomkins@shef.ac.uk, nikul@ee.columbia.edu, yiyin@ee.columbia.edu'
MAINTAINER =         'Yiyin Zhou'
MAINTAINER_EMAIL =   'yiyin@ee.columbia.edu'
DESCRIPTION =        'Fruit Fly Brain Observatory processor component'
URL =                'https://github.com/fruitflybrain/ffbo.processor'
LONG_DESCRIPTION =   DESCRIPTION
DOWNLOAD_URL =       URL
LICENSE =            'BSD'
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development']

# Explicitly switch to parent directory of setup.py in case it
# is run from elsewhere:
os.chdir(os.path.dirname(os.path.realpath(__file__)))
PACKAGES =           find_packages()

if __name__ == "__main__":
    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    setup(
        name = NAME,
        version = VERSION,
        author = AUTHOR,
        author_email = AUTHOR_EMAIL,
        license = LICENSE,
        classifiers = CLASSIFIERS,
        description = DESCRIPTION,
        long_description = LONG_DESCRIPTION,
        url = URL,
        maintainer = MAINTAINER,
        maintainer_email = MAINTAINER_EMAIL,
        packages = PACKAGES,
        include_package_data = True,
        install_requires = [
           'crossbar >= 17.2.1',
           'autobahn[twisted]',
           'configparser',
           'pandas',
           'beautifulsoup4',
           'tinydb',
           'simplejson',
        ],
        eager_resources = ['components/processor_component/data/auth_dict.json', 'components/processor_component/data/email_dict.json']
        )
