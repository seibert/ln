from ln.backend.selector import Selector, parse_selector, create_selector
from ln.backend.datatype import Datatype
from ln.backend.interpolation import none as interp_none
from ln.backend.interpolation import previous as interp_previous
from ln.backend.reduction import sum as reduce_sum
from ln.backend.reduction import closest as reduce_closest
from ln.backend.exception import BadSelectorError

from datetime import datetime
import numpy as np
import pytest


def test_selector_init():
    d = Datatype('int32')
    s = Selector('name', d, 'sum', 'zero', reduce_sum, interp_none)
    assert s.series_name == 'name'
    assert s.datatype == d
    assert s.reduction == 'sum'
    assert s.interpolation == 'zero'
    assert s.reduction_func == reduce_sum
    assert s.interpolation_func == interp_none


def test_parse_selector():
    assert parse_selector('foo') == ('foo', None, None)
    assert parse_selector('foo:sum') == ('foo', 'sum', None)
    assert parse_selector('foo:sum:previous') == ('foo', 'sum', 'previous')


def test_parse_selector_fail():
    with pytest.raises(BadSelectorError):
        parse_selector('foo:bar:baz:boo')


def test_create_selector_defaults():
    config = dict(name='foo', datatype='int32', reduction='sum',
        interpolation='none')
    s = create_selector(config)
    assert s.series_name == 'foo'
    assert s.datatype.is_int_scalar()
    assert s.datatype.base == 'int32'
    assert s.reduction == 'sum'
    assert s.interpolation == 'none'
    assert s.reduction_func == reduce_sum
    assert s.interpolation_func == interp_none


def test_create_selector_override_reduction():
    config = dict(name='foo', datatype='int32', reduction='sum',
        interpolation='none')
    s = create_selector(config, reduction='closest')
    assert s.series_name == 'foo'
    assert s.datatype.is_int_scalar()
    assert s.datatype.base == 'int32'
    assert s.reduction == 'closest'
    assert s.interpolation == 'none'
    assert s.reduction_func == reduce_closest
    assert s.interpolation_func == interp_none


def test_create_selector_override_interpolation():
    config = dict(name='foo', datatype='int32', reduction='sum',
        interpolation='none')
    s = create_selector(config, interpolation='previous')
    assert s.series_name == 'foo'
    assert s.datatype.is_int_scalar()
    assert s.datatype.base == 'int32'
    assert s.reduction == 'sum'
    assert s.interpolation == 'previous'
    assert s.reduction_func == reduce_sum
    assert s.interpolation_func == interp_previous


def test_create_selector_override_both():
    config = dict(name='foo', datatype='int32', reduction='sum',
        interpolation='none')
    s = create_selector(config, reduction='closest', interpolation='previous')
    assert s.series_name == 'foo'
    assert s.datatype.is_int_scalar()
    assert s.datatype.base == 'int32'
    assert s.reduction == 'closest'
    assert s.interpolation == 'previous'
    assert s.reduction_func == reduce_closest
    assert s.interpolation_func == interp_previous


def test_apply_strategies():
    config = dict(name='foo', datatype='int32', reduction='sum',
        interpolation='zero')
    s = create_selector(config)

    # Dummy time
    t = datetime(2013, 8, 26, 11, 0, 0)

    center_times = [datetime(2013, 8, 26, i + 1, 0, 0) for i in range(5)]
    groups = [[(t, 1), (t, 5), (t, 10)],
        [(t, 2), (t, 2)], [], [(t, 1)], [(t, 4), (t, 5), (t, 6)]]
    resampled_values = s.apply_strategies(center_times, groups)
    assert np.array_equal(resampled_values, [16, 4, 0, 1, 15])
