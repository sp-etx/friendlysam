# -*- coding: utf-8 -*-

import os
from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='friendlysam',
    version='0a0',
    packages=['friendlysam'],
    url='http://friendly-sam.readthedocs.org',
    license='LGPLv3',
    author='Rasmus Einarsson',
    author_email='rasmus.einarsson@sp.se',
    description='Toolbox for optimization-based modelling and simulation.',
    long_description=long_description,
    install_requires=[
        'PuLP==1.5.8',
        'networkx==1.9.1'
    ],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3'
    ]
    )