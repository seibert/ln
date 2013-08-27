'''Compatibility methods to support various Python versions'''

# Needed for get_total_seconds() implementation
from __future__ import division


# Implementation for python 2.6
def get_total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
