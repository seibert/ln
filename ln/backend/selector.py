'''Parse and represent Natural Log selectors.'''

from ln.backend.exception import BadSelectorError
from ln.backend.datatype import parse_datatype
from ln.backend.reduction import REDUCTIONS
from ln.backend.interpolation import INTERPOLATIONS


class Selector(object):
    '''A representation of a Natural Log selector.

    A selector consists of:
      * A data series name
      * A Datatype object
      * A Reduction function
      * An Interpolation function
    '''

    def __init__(self, series_name, datatype, reduction, interpolation,
        reduction_func, interpolation_func):
        '''Create a new selector.

        :param series_name: Name of the data series
        :param datatype: ln.backend.datatype.Datatype for this series
        :param reduction: String name of reduction strategy
        :param interpolation: String name of interpolation strategy
        :param reduction_func: Function that implements reduction strategy
        :param interpolation_func: Function that implements interpolation
            strategy
        '''
        self.series_name = series_name
        self.datatype = datatype
        self.reduction = reduction
        self.interpolation = interpolation
        self.reduction_func = reduction_func
        self.interpolation_func = interpolation_func

    def apply_strategies(self, center_times, point_groups):
        '''Compute the resampled value for each point using the provided
        groups of values.

        :center_times: Array of datetime objects representing the center
            of each time bin.
        :point_groups: List of lists of raw points.  Each list element
            (another list) corresponds to raw points in one time bin.  Each
            raw point is a tuple of the form (datetime, value).

        Returns: List of resampled values.
        '''

        # First reduce each bin
        reduced_values = []
        for center_time, group in zip(center_times, point_groups):
            if len(group) == 0:
                reduced_values.append(None)
            else:
                times = []
                values = []
                for t, v in group:
                    times.append(t)
                    values.append(v)
                reduced_value = self.reduction_func(times, values, center_time)
                reduced_values.append(reduced_value)

        # Then interpolate empty bins
        resampled_values = self.interpolation_func(reduced_values,
            self.datatype, center_times)

        return resampled_values


def parse_selector(selector_string):
    '''Parse a selector string and return a tuple of parts, with ``None``
    set for missing parts.

    :param selector_string: String representation of series selector.

    Returns: name, reduction, interpolation
    '''
    parts = selector_string.split(':')
    if len(parts) == 1:
        return parts[0], None, None
    elif len(parts) == 2:
        return parts[0], parts[1], None
    elif len(parts) == 3:
        return parts[0], parts[1], parts[2]
    else:
        raise BadSelectorError('Selector string "%s" has wrong number of parts'
             % selector_string)


def create_selector(series_config, reduction=None, interpolation=None):
    '''Create a Selector representing the given parts.

    :param series_config: dict of series properties
    :param reduction: String name of requested reduction strategy, or ``None``
        to select the default for this series.
    :param interpolation: String name of requested reduction strategy, or
        ``None`` to select the default for this series.
    '''
    name = series_config['name']
    datatype = parse_datatype(series_config['type'])
    if reduction is None:
        reduction = series_config['reduction']
    if interpolation is None:
        interpolation = series_config['interpolation']

    try:
        reduction_func = REDUCTIONS[reduction]
    except KeyError:
        raise BadSelectorError('Unknown reduction "%s"' % reduction)

    try:
        interpolation_func = INTERPOLATIONS[interpolation]
    except KeyError:
        raise BadSelectorError('Unknown interpolation "%s"' % interpolation)

    return Selector(series_name=name, datatype=datatype, reduction=reduction,
        interpolation=interpolation, reduction_func=reduction_func,
        interpolation_func=interpolation_func)
