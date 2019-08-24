import unittest
import os
from setuptools import setup, find_packages
from distutils.core import Command

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")
REQFILE = 'requirements.txt'

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
]

with open(README, 'r') as f:
    long_description = f.read()

with open(REQFILE, 'r') as fh:
    dependencies = fh.readlines()

setup(
    name='text_game_map_maker',
    version='0.1.0',
    description=('Graphical tool for building maps to be used with text_game_maker'),
    long_description=long_description,
    url='http://github.com/eriknyquist/text_game_map_maker',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    install_requires=dependencies,
    packages=['text_game_map_maker'],
    package_data={'text_game_map_maker':['images/logo.png']},
    include_package_data=True,
    zip_safe=False
)
