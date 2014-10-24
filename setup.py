#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='isomedia',
    version='0.2',
    description='This is another ISO base media format file parser.',
    author='Felix Fung',
    author_email='felix.the.cheshire.cat@gmail.com',
    url='https://github.com/flxf/isomedia',
    packages=find_packages(exclude=['tests']),
    install_requires=[],

    keywords=['mp4', 'isom'],
)
