# -*- coding: utf-8 -*-

import os
from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='friendlysam',
    version='',
    packages=['friendlysam'],
    url='',
    license='',
    author='',
    author_email='',
    description='',
    install_requires=required
    )