import pytest
from ln.backend.exception import BackendError
from ln.backend.base import Blob, Backend, get_backend


def test_base_exceptions():
    b = Backend()
    with pytest.raises(BackendError):
        b.create_series('blah', 'blah', 'blah', 'blah',
            'blah', 'blah', 'blah')
    with pytest.raises(BackendError):
        b.get_series_list()
    with pytest.raises(BackendError):
        b.get_config('blah')
    with pytest.raises(BackendError):
        b.update_config('blah')
    with pytest.raises(BackendError):
        b.add_data('blah', 'blah', 'blah')
    with pytest.raises(BackendError):
        b.get_data('blah')
    with pytest.raises(BackendError):
        b.query('blah', 'blah', 'blah', 'blah')
    with pytest.raises(BackendError):
        b.query_continuous('blah', 'blah', 'blah')


def test_get_backend_memory():
    b = get_backend({'backend': 'memory'})
    assert len(b.get_series_list()) == 0


def test_get_backend_sql(tmpdir):
    url = 'sqlite:///' + str(tmpdir.join('test.sqlite'))
    b = get_backend({'backend': 'sql', 'url': url})
    assert len(b.get_series_list()) == 0


def test_blob_exception():
    blob = Blob(index=1, mimetype='text/plain')
    with pytest.raises(BackendError):
        blob.get_bytes()
