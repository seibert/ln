import pytest
import json
from ln.backend import get_backend
import ln.server

sample_config = dict(
        name='node01.cpu_temp',
        type='float32',
        reduction='mean',
        interpolation='linear',
        description='Temperature of CPU in node01',
        unit='deg F',
        metadata='empty'
    )


@pytest.fixture
def app(request):
    ln.server.app.config['TESTING'] = True
    ln.server.storage_backend = get_backend({'backend': 'memory'})
    return ln.server.app.test_client()


def test_root(app):
    res = json.loads(app.get('/').data)
    assert res == {'names': []}

    # Now add a series
    from ln.server import storage_backend
    storage_backend.create_series(**sample_config)

    res = json.loads(app.get('/').data)
    assert res == {'names': [sample_config['name']]}


def test_create(app):
    res = json.loads(app.post('/create', data=sample_config).data)
    assert res == {'result': 'ok'}

    from ln.server import storage_backend
    config = storage_backend.get_config(sample_config['name'])
    assert config == sample_config


def test_get_config(app):
    from ln.server import storage_backend
    storage_backend.create_series(**sample_config)

    res = json.loads(app.get('/data/%s/config' % sample_config['name']).data)
    assert res == sample_config


def test_get_config_fail(app):
    # This config does not exist
    res = app.get('/data/%s/config' % sample_config['name'])
    assert res.status_code == 404


def test_update_config(app):
    from ln.server import storage_backend
    storage_backend.create_series(**sample_config)

    update_request = {
    'unit': 'deg C',
    'description': 'use metric',
    'metadata': 'new'
    }
    res = json.loads(app.post('/data/%s/config' % sample_config['name'],
                                data=update_request).data)
    assert res['result'] == 'ok'

    config = storage_backend.get_config(sample_config['name'])
    for key in update_request:
        assert config[key] == update_request[key]


def test_update_config_incorrect_request(app):
    from ln.server import storage_backend
    storage_backend.create_series(**sample_config)

    update_request = {
    'unit': 'deg C',
    'metadata': 'new'
    }
    res = app.post('/data/%s/config' % sample_config['name'],
                                data=update_request)
    assert res.status_code == 400
    assert json.loads(res.data)['result'] == 'fail'
