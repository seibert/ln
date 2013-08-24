'''Interface for storage backends.'''
from ln.backend.exception import BackendError

class Blob(object):
    '''Base class that represents a blob object in the database.'''

    def __init__(self, index, mimetype):
        self.index = index
        self.mimetype = mimetype

    def get_bytes(self):
        '''Returns the contents of a blob.

        Do not fetch the contents of the blob before this function is called!
        '''
        raise BackendError('Cannot call get_bytes on base class.')


class Backend(object):
    '''A storage backend interface.'''
    def __init__(self):
        pass

    def get_series_list(self):
        '''Returns list of series names'''
        raise BackendError('Cannot call get_series_list on base class.')

    def create_series(self, name, type, reduction, interpolation, unit,
            description, metadata):
        '''Creates a new data series.

        :param name: Name of data series
        :param type: Datatype string describing elements of the series
        :param reduction: Name of default reduction strategy for series
        :param interpolation: Name of default interpolation strategy for series
        :param unit: Unit of series elements
        :param description: Description of series
        :param metadata: Application-specific text metadata about series.
        '''
        raise BackendError('Cannot call create_series on base class.')

    def get_config(self, name):
        '''Returns a dictionary of the data series configuration, or None
        if the series does not exist.

        :param name: Name of series.
        '''
        raise BackendError('Cannot call get_config on base class.')

    def update_config(self, name, unit=None, description=None, metadata=None):
        '''Updates the configuration of a data series.

        :param name: Name of data series
        :param unit: New value for series units
        :param description: New value for series description
        :param metadata: New value for series metadata

        If you want to change any of the config values to be empty, set it to
        the empty string, rather than None.
        '''
        raise BackendError('Cannot call update_config on base class.')

    def add_data(self, name, time, value):
        '''Adds a point to data series.

        :param name: Name of data series
        :param time: timestamp of point
        :type time: datetime.datetime
        :param value: Data point (type depends on type of series)

        Returns the integer sequence number of this new point in the series.'''
        raise BackendError('Cannot call add_data on base class.')

    def get_data(self, name, offset=None, limit=None):
        '''Get raw data points.

        :param name: Name of data series
        :param offset: Sequence number of first data point to return.
        :param limit: Maximum number of points to return.

        Returns ``(times, values, resume)`` tuple, where ``times`` is
        a list of datetime objects, ``values`` is a list
        of values corresponding to those timestamps, and resume is the
        sequence number of the point in the database after the last returned
        point, or None if no more elements (helps with pagination).'''
        raise BackendError('Cannot call get_data on base class.')

    def query(self, selectors, first, last, npoints):
        '''Query the database between the given time interval.

        :param selectors: List of query selectors, one per data series.
        :param first: Time stamp of earliest data to include.  Note that
                      the database will make a best effort to honor this.
        :type first: datetime.datetime

        :param last: Time stamp of the latest data to include.  Note that
                      the database will make a best effort to honor this.
        :type laste: datetime.Datetime

        :param npoints: Approximate number of summary points to return.

        Returns: ``(times, values)``, where ``times`` is a 1D
        array of timestamps, and ``values`` is a list of lists, one per
        timestamp.  Each list contains the values for each series in the order
        they were listed in ``selectors``.
        '''
        raise BackendError('Cannot call query on base class.')

    def query_continuous(self, selectors, first, npoints):
        '''Query database between time ``first`` and now, returning
        approximately npoints of data, and a generator that produces new
        points with the same sampling interval.

        :param selectors: List of query selectors, one per data series.
        :param first: Time stamp of earliest data to include.
        :type first: datetime.datetime

        :param npoints: Approximate number of points between ``first`` and
                        now to return immediately.

        Returns ``(times, values, generator)``, where ``times`` and ``values``
        are the immediate result of the query, and ``generator`` emits
        ``(times, values)`` tuples periodically with new points.  In both
        cases, ``times`` is a list of timestamps, and ``values`` is a list of
        lists, even if there is only 1 row to return.

        Note that the returned generator will block while waiting for new
        data, so do not call it from your main thread!
        '''
        raise BackendError('Cannot call query_continuous on base class.')


def get_backend(storage_config):
    '''Find/build a backend based on the configuration.

    :param config: storage section of the configuration
    '''
    storage_type = storage_config['backend']
    if storage_type == 'memory':
        from ln.backend.sql import SQLBackend
        return SQLBackend('sqlite://')
    if storage_type == 'sql':
        from ln.backend.sql import SQLBackend
        return SQLBackend(storage_config['url'])
