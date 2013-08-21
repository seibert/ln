import json
import requests
import utils

def test_create():
    '''Test creation of data sources.'''
    test_data = {
        'name': 'testname',
        'type': 'float32',
        'reduction': 'mean',
        'interpolation': 'linear',
        'unit': '',
        'description': 'this is a test'}

    host, port, base = utils.get_config_urls()

    post_url = 'http://%s:%i/create' % (host, port)
    print post_url, base
    r = requests.post(post_url, data=test_data)
    assert r.status_code == 200

    r = requests.get(base)
    assert r.status_code == 200

    assert 'testname' in r.json()['names']

