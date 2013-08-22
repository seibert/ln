import pytest
from ln.backend.exception import BadTypeError
from ln.backend.datatype import parse_datatype, Datatype


def test_parse_scalar_datatype():
    for scalar in ['int8', 'int16', 'int32', 'float32', 'float64']:
        d = parse_datatype(scalar)
        assert d.base == scalar
        assert d.is_scalar()
        assert not d.is_array()
        assert not d.is_blob()


def test_parse_array_datatype():
    d = parse_datatype('float64[10]')
    assert not d.is_scalar()
    assert d.is_array()
    assert not d.is_blob()
    assert d.base == 'float64'
    assert d.shape == (10,)

    d = parse_datatype('int8[10,10]')
    assert not d.is_scalar()
    assert d.is_array()
    assert not d.is_blob()
    assert d.base == 'int8'
    assert d.shape == (10, 10)

    # Check spaces
    d = parse_datatype('int16[ 10,  1  , 40]')
    assert not d.is_scalar()
    assert d.is_array()
    assert not d.is_blob()
    assert d.base == 'int16'
    assert d.shape == (10, 1, 40)


def test_parse_blob_datatype():
    d = parse_datatype('blob:image/png')
    assert not d.is_scalar()
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
        Datatype('blob', shape=(1,2), mimetype='image/png')
    with pytest.raises(BadTypeError):
        Datatype('blob')

def test_check_shape():
    d = Datatype('int8', shape=(2,3))
    assert not d.check_shape([1, 2])
    assert not d.check_shape([1, 2, 3])
    assert d.check_shape([[1, 2, 3], [4, 5, 6]])
    assert not d.check_shape([[1, 2], [3, 4], [5, 6]])
