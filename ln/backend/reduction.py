'''Functions that perform the different reduction strategies.'''

# Needed for get_total_seconds() implementation
from __future__ import division

import numpy as np


# Implementation for python 2.6
def get_total_sections(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


def closest(times, values, center_time):
    abs_delta = np.abs(np.array([get_total_sections(t - center_time)
        for t in times]))
    closest_index = np.argmin(abs_delta)
    return values[closest_index]


def sum(times, values, center_time):
    return np.sum(values, axis=0)


def mean(times, values, center_time):
    return np.mean(values, axis=0)


def min(times, values, center_time):
    return np.amin(values, axis=0)


def max(times, values, center_time):
    return np.amax(values, axis=0)


REDUCTIONS = dict(closest=closest, sum=sum, mean=mean, min=min, max=max)
