from ln.backend import reduction
from datetime import datetime
import pytest


@pytest.fixture
def group():
    times = [datetime(2013, 8, 26, i + 1, 0, 0) for i in range(5)]
    values = [1, 2, 3, 4, 5]
    center_time = datetime(2013, 8, 26, 1, 40, 0)
    return dict(times=times, values=values, center_time=center_time)


def test_closest(group):
    assert reduction.closest(**group) == 2


def test_sum(group):
    assert reduction.sum(**group) == 15


def test_mean(group):
    assert reduction.mean(**group) == 3


def test_min(group):
    assert reduction.min(**group) == 1


def test_max(group):
    assert reduction.max(**group) == 5
