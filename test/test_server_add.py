import ln.server
from ln.backend import get_backend
from ln.backend.compat import get_total_seconds
from datetime import datetime, timedelta
import pytest
import numpy as np
import json


try:  # Python 2
    from StringIO import StringIO as BytesIO
except ImportError:  # Python 3
    from io import BytesIO


@pytest.fixture
def app(request):
    ln.server.app.config['TESTING'] = True
    ln.server.app.config['url_base'] = ''
    ln.server.storage_backend = get_backend({'backend': 'memory'})
    b = ln.server.storage_backend
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
    return ln.server.app.test_client()


def get_json_and_status(request):
    return json.loads(request.get_data(as_text=True)), request.status_code


def test_add_doesnotexist(app):
    data = dict(time=datetime.now().isoformat(), value=1)
    response, code = get_json_and_status(app.post('/data/doesnotexist',
        data=data))
    assert code == 404


def test_get_doesnotexist(app):
    response, code = get_json_and_status(app.get('/data/doesnotexist'))
    assert code == 404


def test_get_last(app):
    b = ln.server.storage_backend
    times = []
    for i in range(10):
        times.append(datetime.now())
        b.add_data('int', times[-1], i)

    data = dict()
    response, code = get_json_and_status(app.get('/data/int'))
    assert code == 200

    assert len(response['times']) == 1
    assert len(response['values']) == 1
    assert 'resume' not in response
    assert times[-1].isoformat() == response['times'][0]
    assert 9 == response['values'][0]


def test_get_limit(app):
    b = ln.server.storage_backend
    times = []
    for i in range(10):
        times.append(datetime.now())
        b.add_data('int', times[-1], i)

    response, code = get_json_and_status(app.get('/data/int?offset=1&limit=2'))
    assert code == 200

    assert len(response['times']) == 2
    assert len(response['values']) == 2
    assert response['resume'] == 3
    assert [t.isoformat() for t in times[1:3]] == response['times']
    assert [1, 2] == response['values']

    response, code = get_json_and_status(app.get('/data/int?offset=9&limit=2'))
    assert code == 200

    assert len(response['times']) == 1
    assert len(response['values']) == 1
    assert 'resume' not in response
    assert [times[-1].isoformat()] == response['times']
    assert [9] == response['values']


def test_get_id_no_series(app):
    # This config does not exist
    res = app.get('/data/noexist/1')
    assert res.status_code == 404


def test_get_id_no_id(app):
    # This config does not exist
    res = app.get('/data/int/1')
    assert res.status_code == 404


def test_add_int(app):
    b = ln.server.storage_backend
    times = []
    for i in range(10):
        times.append(datetime.now())

        data = dict(time=times[-1].isoformat(), value=i)
        response, code = get_json_and_status(app.post('/data/int', data=data))
        assert code == 200
        assert response['index'] == i
        assert response['url'] == '/data/int/%d' % i

    db_times, db_values, next_seq = b.get_data('int', 0)
    assert times == db_times
    assert list(range(10)) == db_values
    assert next_seq is None

    response = app.get('/data/int/9')
    assert json.loads(response.get_data(as_text=True)) == 9


def test_add_float(app):
    b = ln.server.storage_backend
    times = []
    for i in range(10):
        times.append(datetime.now())

        data = dict(time=times[-1].isoformat(), value=i + 0.5)
        response, code = get_json_and_status(app.post('/data/float', data=data))
        assert code == 200
        assert response['index'] == i
        assert response['url'] == '/data/float/%d' % i

    db_times, db_values, next_seq = b.get_data('float', 0)
    assert times == db_times
    assert [i + 0.5 for i in range(10)] == db_values
    assert next_seq is None


def test_add_array(app):
    b = ln.server.storage_backend
    times = []
    values = []
    for i in range(10):
        times.append(datetime.now())
        values.append(np.array(range(4)) * i)

        data = dict(time=times[-1].isoformat(), value=json.dumps(values[-1].tolist()))
        response, code = get_json_and_status(app.post('/data/array', data=data))
        assert code == 200
        assert response['index'] == i
        assert response['url'] == '/data/array/%d' % i

    db_times, db_values, next_seq = b.get_data('array', 0)
    assert times == db_times
    assert np.array_equal(np.array(values), np.array(db_values))
    assert next_seq is None

    response = app.get('/data/array/9')
    assert np.array_equal(json.loads(response.get_data(as_text=True)),
        values[9])


def test_add_blob(app):
    b = ln.server.storage_backend
    times = []
    values = []
    urls = []
    for i in range(10):
        times.append(datetime.now())
        values.append(b'-' * 10)

        byte_source = BytesIO(values[-1])
        data = dict(time=times[-1].isoformat(), value=(byte_source, 'file'))
        response, code = get_json_and_status(app.post('/data/blob', data=data))
        assert code == 200
        assert response['index'] == i
        assert response['url'] == '/data/blob/%d' % i
        urls.append(response['url'])

    # Test fetching last blob
    response, code = get_json_and_status(app.get('/data/blob'))
    assert code == 200
    assert response['values'][0] == '/data/blob/9'
    response = app.get('/data/blob/9')
    assert response.data == values[9]
    assert response.mimetype == 'text/plain'

    db_times, db_values, next_seq = b.get_data('blob', 0)
    assert times == db_times
    assert np.array_equal(range(10), [b.index for b in db_values])  # Index numbers
    assert next_seq is None


def test_add_wrong_order(app):
    now = datetime.now()

    data = dict(time=now.isoformat(), value=1)
    response, code = get_json_and_status(app.post('/data/int', data=data))
    assert code == 200

    data = dict(time=(now - timedelta(hours=1)).isoformat(), value=1)
    response, code = get_json_and_status(app.post('/data/int', data=data))
    assert code == 400
    assert response['type'] == 'time_order'


def test_add_bad_type(app):
    data = dict(time=datetime.now().isoformat(), value='[1, 2]')
    response, code = get_json_and_status(app.post('/data/int', data=data))
    assert code == 400
    assert response['type'] == 'bad_type'


def test_add_now(app):
    b = ln.server.storage_backend
    now = datetime.now()
    data = dict(value=1)
    response, code = get_json_and_status(app.post('/data/int', data=data))
    assert code == 200
    assert response['index'] == 0

    db_times, db_values, next_seq = b.get_data('int', 0)
    assert get_total_seconds(db_times[0] - now) < 0.01
    assert db_values[0] == 1
