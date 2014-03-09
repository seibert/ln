'''Compatibility methods to support various Python versions'''

# Needed for get_total_seconds() implementation
from __future__ import division
import sys

# Implementation for python 2.6
def get_total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

version = sys.version_info[:2]
zip = zip
if version < (3,0):
    import itertools
    zip = itertools.izip

