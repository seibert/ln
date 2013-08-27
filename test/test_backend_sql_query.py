from ln.backend.sql import SQLBackend
from ln.backend.exception import BadSelectorError
from datetime import datetime, timedelta
import pytest
import numpy as np
from itertools import islice


@pytest.fixture
def backend():
    b = SQLBackend('sqlite://')
    int_config = dict(
        name='int',
        type='int32',
        reduction='sum',
        interpolation='zero',
        description='Integer counter',
        unit='',
        metadata=''
    )
    b.create_series(**int_config)

    start = datetime(2013, 8, 26, 0, 0, 0)
    b.add_data('int', start + timedelta(hours=1), 1)
    b.add_data('int', start + timedelta(hours=2, minutes=29, seconds=59), 3)
    b.add_data('int', start + timedelta(hours=2, minutes=30), 10)
    b.add_data('int', start + timedelta(hours=3), 20)
    b.add_data('int', start + timedelta(hours=3, minutes=10), 1)
    b.add_data('int', start + timedelta(hours=5), 2)
    b.add_data('int', start + timedelta(hours=6), 6)
    return b


def test_query_basic(backend):
    first = datetime(2013, 8, 26, 0, 0, 0)
    last = datetime(2013, 8, 26, 11, 0, 0)

    times, values = backend.query(['int'], first, last, 12)
    assert len(times) == 12
    assert np.array_equal(values, [[0, 1, 3, 31, 0, 2, 6, 0, 0, 0, 0, 0]])

    times, values = backend.query(['int'], first, last, 6)
    assert len(times) == 6
    assert np.array_equal(values, [[1, 34, 2, 6, 0, 0]])


def test_bad_query(backend):
    first = datetime(2013, 8, 26, 0, 0, 0)
    last = datetime(2013, 8, 26, 11, 0, 0)

    with pytest.raises(BadSelectorError):
        backend.query(['doesnotexist'], first, last, 12)

    with pytest.raises(BadSelectorError):
        backend.query(['int:blah'], first, last, 12)

    with pytest.raises(BadSelectorError):
        backend.query(['int:sum:blah'], first, last, 12)


def test_query_continuous(backend):
    delta_t = timedelta(milliseconds=10)
    first = datetime.now() - delta_t

    times, values, gen = backend.query_continuous(['int'], first, 2)

    for i in range(2, 6):
        backend.add_data('int', first + i * delta_t, i)

    for i, (times, values) in enumerate(islice(gen, 4)):
        assert len(times) == 1
        assert len(values[0]) == 1
        assert values[0][0] == i + 2
