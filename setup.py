from setuptools import setup
import sys
import os

sys.path.insert(0, '.')
from ln import __version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

install_requires = ['flask', 'requests', 'pytest']
# Trick lifted from tox setup.py
version = sys.version_info[:2]
if version < (2,7) or (3,0) <= version <= (3,1):
    install_requires.append('argparse')

setup(
    name = "ln",
    version = __version__,
    description = ("Natural Log is a time-series database with a REST API."),
    url = "http://github.com/seibert/ln",
    #long_description = read('README.md'),
    packages = ['ln'],
    scripts = ['bin/ln-server'],
    install_requires = ['flask', 'requests', 'pytest']
)

