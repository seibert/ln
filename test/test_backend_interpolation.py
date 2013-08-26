from ln.backend import interpolation
from ln.backend.datatype import Datatype
import numpy as np
import pytest


def test_none():
    a = [1, 3, None, 4, None]
    assert np.array_equal(interpolation.none(a, None, None), a)


def test_zero():
    d = Datatype('int32')
    a = [1, 3, None, 4, None]
    result = interpolation.zero(a, d, None)
    assert np.array_equal(result, [1, 3, 0, 4, 0])


def test_previous():
    d = Datatype('int32')
    a = [1, 3, None, 4, None]
    result = interpolation.previous(a, d, None)
    assert np.array_equal(result, [1, 3, 3, 4, 4])


@pytest.mark.xfail
def test_linear():
    d = Datatype('float32')
    a = [1.0, 3.0, None, 4.0, None]
    assert np.array_equal(interpolation.linear(a, d, None),
        [1.0, 3.0, 3.5, 4.0, 4.0])
