import pytest
import json
from datetime import datetime, timedelta
import numpy as np

from ln.backend import get_backend
import ln.server


@pytest.fixture
def app():
    ln.server.app.config['TESTING'] = True
    ln.server.storage_backend = get_backend({'backend': 'memory'})

    # Prepopulate with some data
    b = ln.server.storage_backend
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

    return ln.server.app.test_client()


def test_query_basic(app):
    first = datetime(2013, 8, 26, 0, 0, 0)
    last = datetime(2013, 8, 26, 11, 0, 0)

    result = json.loads(app.get('/query?selector=int&first=%s&last=%s&npoints=12'
        % (first.isoformat(), last.isoformat())).get_data(as_text=True))

    times, values = result['times'], result['values']
    assert len(times) == 12
    assert np.array_equal(values, [[0, 1, 3, 31, 0, 2, 6, 0, 0, 0, 0, 0]])

    result = json.loads(app.get('/query?selector=int&first=%s&last=%s&npoints=6'
        % (first.isoformat(), last.isoformat())).get_data(as_text=True))
    times, values = result['times'], result['values']
    assert len(times) == 6
    assert np.array_equal(values, [[1, 34, 2, 6, 0, 0]])


def test_query_fail_missing_field(app):
    result = app.get('/query?selector=int&first=foo&last=bar')
    assert result.status_code == 400


def test_query_fail_bad_timestamp(app):
    result = app.get('/query?selector=int&first=foo&last=bar&npoints=3')
    assert result.status_code == 400


def test_query_fail_bad_npoints(app):
    result = app.get('/query?selector=int&first=foo&last=bar&npoints=1')
    assert result.status_code == 400


def test_query_fail_bad_time_order(app):
    first = datetime(2013, 8, 26, 0, 0, 0)
    last = datetime(2013, 8, 26, 11, 0, 0)

    result = app.get('/query?selector=int&first=%s&last=%s&npoints=4'
        % (last.isoformat(), first.isoformat()))  # intentionally backwards!
    assert result.status_code == 400


def test_query_continuous(app):
    backend = ln.server.storage_backend
    ln.server.app.config['LIMIT_CONTINUOUS'] = 5

    delta_t = timedelta(milliseconds=100)
    first = datetime.now() - delta_t

    times, values, gen = backend.query_continuous(['int'], first, 2)
    response = app.get('/query?selector=int&first=%s&npoints=2'
        % (first.isoformat(),))
    assert response.status_code == 200

    # Quick! Populate backend directly with some data
    for i in range(2, 6):
        backend.add_data('int', first + i * delta_t, i)

    messages = response.get_data(as_text=True).split('data: ')[1:]
    initial = json.loads(messages[0])
    assert len(initial['times']) == 2
    assert initial['values'] == [[0, 0]]

    for i in range(2, 6):
        message = json.loads(messages[i - 1])
        assert len(message['times']) == 1
        assert len(message['values']) == 1
        assert message['values'][0][0] == i
