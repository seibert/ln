from ln.backend.sql import SQLBackend
from ln.backend.exception import SeriesCreationError, SeriesDoesNotExistError
import pytest


def test_create():
    b = SQLBackend('sqlite://')
    assert len(b.get_series_list()) == 0


def test_create_source_scalar():
    b = SQLBackend('sqlite://')
    true_config = dict(
        name='node01.cpu_temp',
        type='float32',
        reduction='mean',
        interpolation='linear',
        description='Temperature of CPU in node01',
        unit='deg F',
        metadata='empty'
    )

    b.create_series(**true_config)

    assert b.get_series_list() == ['node01.cpu_temp']

    config = b.get_config('node01.cpu_temp')
    assert config is not None

    for key, value in true_config.items():
        assert config[key] == value


def test_create_source_conflict():
    b = SQLBackend('sqlite://')
    config = dict(
        name='node01.cpu_temp',
        type='float32',
        reduction='mean',
        interpolation='linear',
        description='Temperature of CPU in node01',
        unit='deg F',
        metadata='empty'
    )
    b.create_series(**config)
    with pytest.raises(SeriesCreationError):
        b.create_series(**config)


def test_get_config_nonexistent():
    b = SQLBackend('sqlite://')
    assert b.get_config('not.there') is None


def test_update_config_nonexistent():
    b = SQLBackend('sqlite://')
    with pytest.raises(SeriesDoesNotExistError):
        b.update_config('not.there', unit='')


def test_update_source():
    b = SQLBackend('sqlite://')
    orig_config = dict(
        name='node01.cpu_temp',
        type='float32',
        reduction='mean',
        interpolation='linear',
        description='Temperature of CPU in node01',
        unit='deg F',
        metadata='empty'
    )
    b.create_series(**orig_config)

    # Original config
    config = b.get_config('node01.cpu_temp')
    for key, value in orig_config.items():
        assert config[key] == value

    # Update config
    b.update_config(name=orig_config['name'], unit='deg C')
    config = b.get_config('node01.cpu_temp')
    assert config['unit'] == 'deg C'
    assert config['description'] == orig_config['description']
    assert config['metadata'] == orig_config['metadata']

    b.update_config(name=orig_config['name'], description='foo')
    config = b.get_config('node01.cpu_temp')
    assert config['unit'] == 'deg C'
    assert config['description'] == 'foo'
    assert config['metadata'] == orig_config['metadata']

    b.update_config(name=orig_config['name'], metadata='[1,10]')
    config = b.get_config('node01.cpu_temp')
    assert config['unit'] == 'deg C'
    assert config['description'] == 'foo'
    assert config['metadata'] == '[1,10]'


def test_create_source_array():
    b = SQLBackend('sqlite://')
    true_config = dict(
        name='node01.rates',
        type='float32',
        reduction='mean',
        interpolation='linear',
        description='Channel rates',
        unit='',
        metadata=''
    )

    b.create_series(**true_config)

    assert b.get_series_list() == ['node01.rates']

    config = b.get_config('node01.rates')
    assert config is not None

    for key, value in true_config.items():
        assert config[key] == value
