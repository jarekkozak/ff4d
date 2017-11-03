# -*- coding: utf-8 -*-

try:
    from setuptools.core import setup
except ImportError:
    from distutils.core import setup

setup(
    name='ff4d',
    version='0.1.0',
    author='Jarosław Kozak',
    author_email='jaroslaw.kozak68@gmail.com',
    packages=['tests'],
    description='Tests setup',
    test_suite='tests.get_suite'
)