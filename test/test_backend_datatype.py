import pytest
import numpy as np
from ln.backend.exception import BadTypeError
from ln.backend.datatype import parse_datatype, Datatype


def test_parse_scalar_datatype():
    for scalar in ['int8', 'int16', 'int32', 'float32', 'float64']:
        d = parse_datatype(scalar)
        assert d.base == scalar
        assert d.is_scalar()
        if 'int' in scalar:
            assert d.is_int_scalar()
            assert not d.is_float_scalar()
        else:
            assert not d.is_int_scalar()
            assert d.is_float_scalar()
        assert not d.is_array()
        assert not d.is_blob()


def test_parse_array_datatype():
    d = parse_datatype('float64[10]')
    assert not d.is_scalar()
    assert not d.is_int_scalar()
    assert not d.is_float_scalar()
    assert d.is_array()
    assert not d.is_blob()
    assert d.base == 'float64'
    assert d.shape == (10,)

    d = parse_datatype('int8[10,10]')
    assert not d.is_scalar()
    assert not d.is_int_scalar()
    assert not d.is_float_scalar()
    assert d.is_array()
    assert not d.is_blob()
    assert d.base == 'int8'
    assert d.shape == (10, 10)

    # Check spaces
    d = parse_datatype('int16[ 10,  1  , 40]')
    assert not d.is_scalar()
    assert not d.is_int_scalar()
    assert not d.is_float_scalar()
    assert d.is_array()
    assert not d.is_blob()
    assert d.base == 'int16'
    assert d.shape == (10, 1, 40)


def test_parse_blob_datatype():
    d = parse_datatype('blob:image/png')
    assert not d.is_scalar()
    assert not d.is_int_scalar()
    assert not d.is_float_scalar()
    assert not d.is_array()
    assert d.is_blob()
    assert d.base == 'blob'
    assert d.mimetype == 'image/png'


def test_parse_bad_scalar():
    with pytest.raises(BadTypeError):
        parse_datatype('foo')


def test_parse_bad_array():
    with pytest.raises(BadTypeError):
        parse_datatype('foo[10]')
    with pytest.raises(BadTypeError):
        parse_datatype('int8[foo]')
    with pytest.raises(BadTypeError):
        parse_datatype('int8[10,foo]')
    with pytest.raises(BadTypeError):
        parse_datatype('int8[10,foo')
    with pytest.raises(BadTypeError):
        parse_datatype('int8[[10]')


def test_parse_bad_blob():
    with pytest.raises(BadTypeError):
        parse_datatype('foo:image/png')


def test_bad_datatype_args():
    with pytest.raises(BadTypeError):
        Datatype('foo')
    with pytest.raises(BadTypeError):
        Datatype('blob', shape=(1, 2), mimetype='image/png')
    with pytest.raises(BadTypeError):
        Datatype('blob')


def test_check_shape():
    d = Datatype('int8', shape=(2, 3))
    assert not d.check_shape([1, 2])
    assert not d.check_shape([1, 2, 3])
    assert d.check_shape([[1, 2, 3], [4, 5, 6]])
    assert not d.check_shape([[1, 2], [3, 4], [5, 6]])


def test_coerce_scalar():
    d = Datatype('int32')
    assert d.coerce(1) == 1
    assert d.coerce(1.5) == 1
    assert d.coerce(np.int8(1)) == 1

    with pytest.raises(BadTypeError):
        d.coerce('foo')

    d = Datatype('float64')
    assert d.coerce(1.5) == 1.5
    assert d.coerce(1) == 1.0
    assert d.coerce(np.float32(1.5)) == 1.5

    with pytest.raises(BadTypeError):
        d.coerce('foo')


def array_equal_with_dtype(a, b):
    '''Returns true if the contents of a and b are the same, as well
    as the dtypes.'''
    return a.dtype == b.dtype and np.array_equal(a, b)


def test_coerce_array():
    d = Datatype('int32', shape=(2,))
    assert array_equal_with_dtype(d.coerce((1, 2)),
        np.array([1, 2], dtype=np.int32))

    assert array_equal_with_dtype(d.coerce((1.5, 2)),
        np.array([1, 2], dtype=np.int32))

    assert array_equal_with_dtype(d.coerce(np.array([1.5, 2], dtype=np.float32)),
        np.array([1, 2], dtype=np.int32))

    with pytest.raises(BadTypeError):
        d.coerce((1.5, 2, 3))


def test_coerce_blob():
    d = Datatype('blob', mimetype='text/plain')
    assert d.coerce(b'foo') == b'foo'
