from setuptools import setup
import sys
import os

sys.path.insert(0, '.')
from ln import __version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "ln",
    version = __version__,
    description = ("Natural Log is a time-series database with a REST API."),
    url = "http://github.com/seibert/ln",
    #long_description = read('README.md'),
    packages = ['ln'],
    scripts = ['bin/ln-server'],
    install_requires = ['flask']
)

