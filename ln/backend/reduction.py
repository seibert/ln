'''Functions that perform the different reduction strategies.'''
import numpy as np


def closest(times, values, center_time):
    abs_delta = np.abs(np.array([(t - center_time).total_seconds()
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
