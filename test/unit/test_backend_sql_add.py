from ln.backend.sql import SQLBackend
from ln.backend.exception import BadTypeError, SeriesDoesNotExistError, \
    SeriesTimeOrderError
from datetime import datetime, timedelta
import pytest
import numpy as np


@pytest.fixture
def backend():
    b = SQLBackend('sqlite://')
    int_config = dict(
        name='int',
        type='int32',
        reduction='sum',
        interpolation='linear',
        description='Integer counter',
        unit='',
        metadata=''
    )
    b.create_series(**int_config)
    float_config = dict(
        name='float',
        type='float32',
        reduction='mean',
        interpolation='linear',
        description='Float counter',
        unit='',
        metadata=''
    )
    b.create_series(**float_config)
    array_config = dict(
        name='array',
        type='float32[4]',
        reduction='mean',
        interpolation='linear',
        description='Array',
        unit='',
        metadata=''
    )
    b.create_series(**array_config)
    blob_config = dict(
        name='blob',
        type='blob:text/plain',
        reduction='closest',
        interpolation='none',
        description='BLOB',
        unit='',
        metadata=''
    )
    b.create_series(**blob_config)
    return b


def test_add_doesnotexist(backend):
    b = backend
    with pytest.raises(SeriesDoesNotExistError):
        b.add_data('doesnotexist', datetime.now(), 1)


def test_get_doesnotexist(backend):
    b = backend
    with pytest.raises(SeriesDoesNotExistError):
        b.get_data('doesnotexist')


def test_get_empty_series(backend):
    b = backend
    db_times, db_values, next_seq = b.get_data('int')
    assert len(db_times) == 0
    assert len(db_values) == 0
    assert next_seq is None


def test_get_last(backend):
    b = backend
    times = []
    for i in range(10):
        times.append(datetime.now())
        b.add_data('int', times[-1], i)

    db_times, db_values, next_seq = b.get_data('int')
    assert len(db_times) == 1
    assert len(db_values) == 1
    assert times[-1] == db_times[0]
    assert 9 == db_values[0]
    assert next_seq is None


def test_get_limit(backend):
    b = backend
    times = []
    for i in range(10):
        times.append(datetime.now())
        b.add_data('int', times[-1], i)

    db_times, db_values, next_seq = b.get_data('int', 1, 2)
    assert len(db_times) == 2
    assert len(db_values) == 2
    assert next_seq == 3
    assert times[1:3] == db_times
    assert [1, 2] == db_values

    db_times, db_values, next_seq = b.get_data('int', 9, 2)
    assert len(db_times) == 1
    assert len(db_values) == 1
    assert next_seq is None
    assert times[-1] == db_times[0]
    assert [9] == db_values


def test_add_int(backend):
    b = backend
    times = []
    for i in range(10):
        times.append(datetime.now())
        index = b.add_data('int', times[-1], i)
        assert index == i

    db_times, db_values, next_seq = b.get_data('int', 0)
    assert times == db_times
    assert list(range(10)) == db_values
    assert next_seq is None


def test_add_float(backend):
    b = backend
    times = []
    for i in range(10):
        times.append(datetime.now())
        index = b.add_data('float', times[-1], i + 0.5)
        assert index == i

    db_times, db_values, next_seq = b.get_data('float', 0)
    assert times == db_times
    assert [i + 0.5 for i in range(10)] == db_values
    assert next_seq is None


def test_add_array(backend):
    b = backend
    times = []
    values = []
    for i in range(10):
        times.append(datetime.now())
        values.append(np.array(range(4)) * i)
        index = b.add_data('array', times[-1], values[-1])
        assert index == i

    db_times, db_values, next_seq = b.get_data('array', 0)
    assert times == db_times
    assert np.array_equal(np.array(values), np.array(db_values))
    assert next_seq is None


def test_add_blob(backend):
    b = backend
    times = []
    values = []
    for i in range(10):
        times.append(datetime.now())
        values.append(b'-' * 10)
        index = b.add_data('blob', times[-1], values[-1])
        assert index == i

    db_times, db_values, next_seq = b.get_data('blob', 0)
    assert times == db_times
    assert values == [b.get_bytes() for b in db_values]
    assert next_seq is None


def test_add_wrong_order(backend):
    b = backend

    now = datetime.now()
    b.add_data('int', now, 1)
    with pytest.raises(SeriesTimeOrderError):
        b.add_data('int', now - timedelta(hours=1), 2)


def test_add_bad_type(backend):
    b = backend
    with pytest.raises(BadTypeError):
        b.add_data('int', datetime.now, [1, 2])
