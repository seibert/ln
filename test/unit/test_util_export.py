from __future__ import unicode_literals

import pytest
import json
import base64
from datetime import datetime

from ln.backend.sql import SQLBackend
from ln.util import export_json
import ln

try:  # Python 2
    from StringIO import StringIO
except ImportError:  # Python 3
    from io import StringIO


@pytest.fixture
def backend():
    b = SQLBackend('sqlite://')

    float_config = dict(
        name='float',
        type='float32',
        reduction='mean',
        interpolation='linear',
        description='Float counter',
        unit='m',
        metadata='blah'
    )
    b.create_series(**float_config)
    array_config = dict(
        name='array',
        type='float32[4]',
        reduction='mean',
        interpolation='linear',
        description='Array',
        unit='cm',
        metadata='test'
    )
    b.create_series(**array_config)
    blob_config = dict(
        name='blob',
        type='blob:text/plain',
        reduction='closest',
        interpolation='none',
        description='BLOB',
        unit='',
        metadata='image'
    )
    b.create_series(**blob_config)
    return b


def basic_contents():
    return {
        'version': ln.__version__,
        'series': [
            {
                'config': {
                    'name': 'float',
                    'type': 'float32',
                    'reduction': 'mean',
                    'interpolation': 'linear',
                    'description': 'Float counter',
                    'unit': 'm',
                    'metadata': 'blah'
                },
                'points': []
            },
            {
                'config': {
                    'name': 'array',
                    'type': 'float32[4]',
                    'reduction': 'mean',
                    'interpolation': 'linear',
                    'description': 'Array',
                    'unit': 'cm',
                    'metadata': 'test'
                },
                'points': []
            },
            {
                'config': {
                    'name': 'blob',
                    'type': 'blob:text/plain',
                    'reduction': 'closest',
                    'interpolation': 'none',
                    'description': 'BLOB',
                    'unit': '',
                    'metadata': 'image'
                },
                'points': []
            },
        ]
    }


def test_export_empty():
    b = SQLBackend('sqlite://')
    out_file = StringIO()
    export_json(b, out_file)

    contents = json.loads(out_file.getvalue())
    expected = {'version': ln.__version__, 'series': []}
    assert contents == expected


def test_export_no_values(backend):
    out_file = StringIO()
    export_json(backend, out_file)

    contents = json.loads(out_file.getvalue())
    expected = basic_contents()
    assert contents == expected


def test_export_scalar(backend):
    backend.add_data('float', datetime(2012, 1, 15, 1, 0, 0), 1.0)
    backend.add_data('float', datetime(2012, 1, 30, 1, 0, 0), 2.0)

    out_file = StringIO()
    export_json(backend, out_file)

    contents = json.loads(out_file.getvalue())
    expected = basic_contents()
    expected['series'][0]['points'] = [
        ['2012-01-15 01:00:00', 1.0],
        ['2012-01-30 01:00:00', 2.0]
    ]
    assert contents == expected


def test_export_array(backend):
    backend.add_data('array',
        datetime(2012, 1, 15, 1, 0, 0), [1.0, 2.0, 3.0, 4.0])
    backend.add_data('array',
        datetime(2012, 1, 30, 1, 0, 0), [2.0, 4.0, 6.0, 8.0])

    out_file = StringIO()
    export_json(backend, out_file)

    contents = json.loads(out_file.getvalue())
    expected = basic_contents()
    expected['series'][1]['points'] = [
        ['2012-01-15 01:00:00', [1.0, 2.0, 3.0, 4.0]],
        ['2012-01-30 01:00:00', [2.0, 4.0, 6.0, 8.0]]
    ]
    assert contents == expected


def test_export_blob(backend):
    blob1 = b'\x00\x01\xff'
    blob2 = b'\x20\x40\x60'
    backend.add_data('blob',
        datetime(2012, 1, 15, 1, 0, 0), blob1)
    backend.add_data('blob',
        datetime(2012, 1, 30, 1, 0, 0), blob2)

    out_file = StringIO()
    export_json(backend, out_file)

    contents = json.loads(out_file.getvalue())
    expected = basic_contents()
    expected['series'][2]['points'] = [
        ['2012-01-15 01:00:00', base64.b64encode(blob1).decode('utf-8')],
        ['2012-01-30 01:00:00', base64.b64encode(blob2).decode('utf-8')]
    ]
    assert contents == expected

